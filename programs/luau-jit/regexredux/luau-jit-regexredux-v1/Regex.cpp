// General PCRE2 compile/find/replace bindings; benchmark sequencing is Luau.
// Suite-authored under Apache-2.0, counted for regex-redux.
#define PCRE2_CODE_UNIT_WIDTH 8
#include <pcre2.h>
#include "lua.h"
#include "lualib.h"
#include <vector>
struct Regex
{
    pcre2_code* code;
    pcre2_match_data* match;
};
static Regex* checked(lua_State* L)
{
    return static_cast<Regex*>(luaL_checkudata(L, 1, "PCRE2"));
}
static int compileRegex(lua_State* L)
{
    size_t size;
    const char* pattern = luaL_checklstring(L, 1, &size);
    int error;
    PCRE2_SIZE offset;
    pcre2_code* code = pcre2_compile(reinterpret_cast<PCRE2_SPTR>(pattern), size, 0, &error, &offset, nullptr);
    if (!code)
        luaL_error(L, "invalid regular expression");
    auto* re = static_cast<Regex*>(lua_newuserdatadtor(L, sizeof(Regex), [](lua_State*, void* p)
    {
        auto* re = static_cast<Regex*>(p);
        pcre2_match_data_free(re->match);
        pcre2_code_free(re->code);
    }));
    re->code = code;
    re->match = pcre2_match_data_create_from_pattern(code, nullptr);
    if (!re->match)
        luaL_error(L, "regex allocation failed");
    int jit = pcre2_jit_compile(code, PCRE2_JIT_COMPLETE);
    if (jit != 0)
        luaL_error(L, "PCRE2 JIT unavailable");
    luaL_getmetatable(L, "PCRE2");
    lua_setmetatable(L, -2);
    return 1;
}
static int findRegex(lua_State* L)
{
    auto* re = checked(L);
    size_t size;
    const char* text = luaL_checklstring(L, 2, &size);
    PCRE2_SIZE offset = static_cast<PCRE2_SIZE>(luaL_optnumber(L, 3, 1) - 1);
    int result = pcre2_match(re->code, reinterpret_cast<PCRE2_SPTR>(text), size, offset, 0, re->match, nullptr);
    if (result == PCRE2_ERROR_NOMATCH)
        return 0;
    if (result < 0)
        luaL_error(L, "regex match failed: %d", result);
    PCRE2_SIZE* span = pcre2_get_ovector_pointer(re->match);
    lua_pushnumber(L, static_cast<double>(span[0] + 1));
    lua_pushnumber(L, static_cast<double>(span[1]));
    return 2;
}
static int replaceRegex(lua_State* L)
{
    auto* re = checked(L);
    size_t size, replacementSize;
    const char* text = luaL_checklstring(L, 2, &size);
    const char* replacement = luaL_checklstring(L, 3, &replacementSize);
    std::vector<unsigned char> output(size + 64);
    PCRE2_SIZE needed = output.size();
    uint32_t flags = PCRE2_SUBSTITUTE_GLOBAL | PCRE2_SUBSTITUTE_OVERFLOW_LENGTH;
    int result = pcre2_substitute(re->code, reinterpret_cast<PCRE2_SPTR>(text), size, 0, flags, re->match, nullptr,
        reinterpret_cast<PCRE2_SPTR>(replacement), replacementSize, output.data(), &needed);
    if (result == PCRE2_ERROR_NOMEMORY)
    {
        output.resize(needed);
        result = pcre2_substitute(re->code, reinterpret_cast<PCRE2_SPTR>(text), size, 0, flags, re->match, nullptr,
            reinterpret_cast<PCRE2_SPTR>(replacement), replacementSize, output.data(), &needed);
    }
    if (result < 0)
        luaL_error(L, "regex replacement failed: %d", result);
    lua_pushlstring(L, reinterpret_cast<const char*>(output.data()), needed);
    return 1;
}
void openRegex(lua_State* L)
{
    luaL_newmetatable(L, "PCRE2");
    lua_pop(L, 1);
    const luaL_Reg functions[] = {{"new", compileRegex}, {"find", findRegex}, {"replace", replaceRegex}, {nullptr, nullptr}};
    luaL_register(L, "regex", functions);
    lua_pop(L, 1);
}
