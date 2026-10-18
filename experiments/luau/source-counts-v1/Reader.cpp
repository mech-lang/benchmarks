// Native Luau lexer and AST inspection; does not execute benchmark source.
#include "Luau/Parser.h"
#include "Luau/Lexer.h"
#include <algorithm>
#include <cstdio>
#include <fstream>
#include <iterator>
#include <map>
#include <set>
#include <string>
struct Owners : Luau::AstVisitor
{
    std::map<unsigned, unsigned> lines;
    bool visit(Luau::AstStat* node) override
    {
        if (!node->is<Luau::AstStatBlock>())
            ++lines[node->location.begin.line + 1];
        return true;
    }
};
int main(int argc, char** argv)
{
    if (argc != 2)
        return 2;
    std::ifstream file(argv[1], std::ios::binary);
    if (!file)
        return 2;
    std::string source{std::istreambuf_iterator<char>(file), std::istreambuf_iterator<char>()};
    Luau::Allocator allocator;
    Luau::AstNameTable names(allocator);
    auto parsed = Luau::Parser::parse(source.data(), source.size(), names, allocator);
    if (!parsed.errors.empty() || !parsed.root)
        return 1;
    Owners owners;
    parsed.root->visit(&owners);
    std::set<unsigned> lines;
    Luau::Lexer lexer(source.data(), source.size(), names);
    lexer.setSkipComments(false);
    for (auto token = lexer.next(); token.type != Luau::Lexeme::Eof; token = lexer.next())
    {
        if (token.type == Luau::Lexeme::Comment || token.type == Luau::Lexeme::BlockComment)
        {
            std::string comment(token.data, token.getLength());
            if (comment.rfind("!native", 0) == 0 || comment.rfind("!optimize", 0) == 0)
                lines.insert(token.location.begin.line + 1);
            continue;
        }
        unsigned last = token.location.end.line + (token.location.end.column != 0);
        for (unsigned line = token.location.begin.line + 1; line <= std::max(last, token.location.begin.line + 1); ++line)
            lines.insert(line);
        if (token.type == Luau::Lexeme::ReservedEnd || token.type == Luau::Lexeme::ReservedElse || token.type == Luau::Lexeme::ReservedUntil)
            ++owners.lines[token.location.begin.line + 1];
    }
    unsigned canonical = 0;
    for (unsigned line : lines)
        canonical += std::max(1u, owners.lines[line]);
    printf("{\"physical_loc\":%zu,\"canonical_loc\":%u,\"token_lines\":[", lines.size(), canonical);
    const char* separator = "";
    for (unsigned line : lines)
    {
        printf("%s%u", separator, line);
        separator = ",";
    }
    printf("],\"owners\":[");
    separator = "";
    for (auto [line, count] : owners.lines)
    {
        printf("%s{\"line\":%u,\"units\":%u}", separator, line, count);
        separator = ",";
    }
    puts("]}");
    return 0;
}
