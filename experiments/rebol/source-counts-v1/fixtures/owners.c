/* Exact owner-boundary fixture, not an extension. */
#define WIDTH 8
static const char module[] =
    "Rebol [Title: {fixture}]\n"
    "f: command [x [integer!]]\n";
enum { A, B,
       C };
int f(void) {
    int a, b;
    a = b = 0;
    for (int i = 0; i < WIDTH; ++i) { a += i; b += i; }
    return a + b;
}
