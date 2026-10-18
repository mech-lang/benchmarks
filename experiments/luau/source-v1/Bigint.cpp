// General GMP integer primitives; the unbounded spigot is implemented in Luau.
// Suite-authored under Apache-2.0, counted for pi digits.
#include <gmp.h>
#include "lua.h"
#include "lualib.h"
static mpz_ptr integer(lua_State* L, int index)
{
    return static_cast<mpz_ptr>(luaL_checkudata(L, index, "Bigint"));
}
static mpz_ptr allocate(lua_State* L)
{
    auto* value = static_cast<mpz_ptr>(lua_newuserdatadtor(L, sizeof(__mpz_struct), [](lua_State*, void* p)
    {
        mpz_clear(static_cast<mpz_ptr>(p));
    }));
    mpz_init(value);
    luaL_getmetatable(L, "Bigint");
    lua_setmetatable(L, -2);
    return value;
}
static int makeInteger(lua_State* L)
{
    long value = static_cast<long>(luaL_checknumber(L, 1));
    mpz_set_si(allocate(L), value);
    return 1;
}
static int add(lua_State* L)
{
    auto a = integer(L, 1);
    auto b = integer(L, 2);
    mpz_add(allocate(L), a, b);
    return 1;
}
static int subtract(lua_State* L)
{
    auto a = integer(L, 1);
    auto b = integer(L, 2);
    mpz_sub(allocate(L), a, b);
    return 1;
}
static int multiply(lua_State* L)
{
    auto a = integer(L, 1);
    if (lua_isnumber(L, 2))
    {
        unsigned long b = static_cast<unsigned long>(luaL_checknumber(L, 2));
        mpz_mul_ui(allocate(L), a, b);
    }
    else
    {
        auto b = integer(L, 2);
        mpz_mul(allocate(L), a, b);
    }
    return 1;
}
static int divide(lua_State* L)
{
    auto a = integer(L, 1);
    auto b = integer(L, 2);
    if (mpz_sgn(b) == 0)
        luaL_error(L, "division by zero");
    mpz_fdiv_q(allocate(L), a, b);
    return 1;
}
static int number(lua_State* L)
{
    lua_pushnumber(L, mpz_get_d(integer(L, 1)));
    return 1;
}
void openBigint(lua_State* L)
{
    luaL_newmetatable(L, "Bigint");
    lua_pop(L, 1);
    const luaL_Reg functions[] = {{"new", makeInteger}, {"add", add}, {"sub", subtract}, {"mul", multiply},
        {"div", divide}, {"number", number}, {nullptr, nullptr}};
    luaL_register(L, "bigint", functions);
    lua_pop(L, 1);
}
