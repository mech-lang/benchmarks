import std/algorithm

func reverseStrings(): array[3, string] =
  result = ["a", "bb", "ccc"]
  reverse(result, 0, 2)

func reverseChars(): array[3, char] =
  result = ['a', 'b', 'c']
  reverse(result, 0, 2)

doAssert reverseStrings() == ["ccc", "bb", "a"]
doAssert reverseChars() == ['c', 'b', 'a']
