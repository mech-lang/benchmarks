// General Luau embedding: source loading, arguments and byte-preserving stdio.
// Suite-authored under Apache-2.0. All authored host source counts in each bundle.
#include "Luau/Compiler.h"
#include "Luau/CodeGen.h"
#include "lua.h"
#include "lualib.h"
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iterator>
#include <string>
#ifdef BENCH_REGEX
void openRegex(lua_State* L);
#endif
#ifdef BENCH_BIGINT
void openBigint(lua_State* L);
#endif

static int readAll(lua_State* L)
{
    std::string data;
    char block[65536];
    while (size_t n = fread(block, 1, sizeof(block), stdin))
        data.append(block, n);
    if (ferror(stdin))
        luaL_error(L, "stdin read failed");
    lua_pushlstring(L, data.data(), data.size());
    return 1;
}

static int writeAll(lua_State* L)
{
    int count = lua_gettop(L);
    for (int i = 1; i <= count; ++i)
    {
        size_t n = 0;
        const char* data = luaL_tolstring(L, i, &n);
        if (fwrite(data, 1, n, stdout) != n)
            luaL_error(L, "stdout write failed");
        lua_pop(L, 1);
    }
    return 0;
}

int main(int argc, char** argv)
{
    if (argc == 2 && strcmp(argv[1], "--version") == 0)
    {
        puts("Luau 0.743 / 9d7748a4f324213a18cb8283fa2a77c330225fa0; source -O2, type info 1; native JIT optional");
        return 0;
    }
    if (argc < 3 || (strcmp(argv[1], "--jit") && strcmp(argv[1], "--vm")))
    {
        fputs("usage: luau-host --vm|--jit source.luau [arguments]\n", stderr);
        return 2;
    }
    bool native = strcmp(argv[1], "--jit") == 0;
    if (native && !Luau::CodeGen::isSupported())
    {
        fputs("native code generation is unavailable\n", stderr);
        return 2;
    }
    std::ifstream file(argv[2], std::ios::binary);
    if (!file)
        return 2;
    std::string source{std::istreambuf_iterator<char>(file), std::istreambuf_iterator<char>()};
    lua_State* L = luaL_newstate();
    luaL_openlibs(L);
    const luaL_Reg io[] = {{"read", readAll}, {"write", writeAll}, {nullptr, nullptr}};
    luaL_register(L, "io", io);
    lua_pop(L, 1);
#ifdef BENCH_REGEX
    openRegex(L);
#endif
#ifdef BENCH_BIGINT
    openBigint(L);
#endif
    lua_createtable(L, argc - 3, 0);
    for (int i = 3; i < argc; ++i)
    {
        lua_pushstring(L, argv[i]);
        lua_rawseti(L, -2, i - 2);
    }
    lua_setglobal(L, "arg");
    luaL_sandbox(L);
    luaL_sandboxthread(L);
    Luau::CompileOptions options;
    options.optimizationLevel = 2;
    options.debugLevel = 0;
    options.typeInfoLevel = 1;
    std::string bytecode = Luau::compile(source, options);
    std::string name = std::string("@") + argv[2];
    int status = luau_load(L, name.c_str(), bytecode.data(), bytecode.size(), 0);
    if (status == 0 && native)
    {
        Luau::CodeGen::create(L);
        Luau::CodeGen::CompilationStats stats;
        auto result = Luau::CodeGen::compile(L, -1, Luau::CodeGen::CompilationOptions{}, &stats);
        if (result.hasErrors() || stats.functionsCompiled == 0)
        {
            fputs("native compilation failed\n", stderr);
            lua_close(L);
            return 2;
        }
    }
    if (status == 0)
        status = lua_pcall(L, 0, 0, 0);
    if (status != 0)
        fprintf(stderr, "%s\n", lua_tostring(L, -1));
    lua_close(L);
    bool outputOK = fflush(stdout) == 0 && !ferror(stdout);
    return status == 0 && outputOK ? 0 : 1;
}
