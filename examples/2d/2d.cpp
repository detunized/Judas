struct Point
{
    Point(int x, int y)
        : x(x)
        , y(y)
    {}

    int x;
    int y;
};

struct Line
{
    Line(Point from, Point to)
        : from(from)
        , to(to)
    {}

    Point from;
    Point to;
};

int main(int argc, char **argv)
{
    Point p1(100, 100);

    asm("int $3"); // break here (on Intel)

    p1.x += 100;

    Line l1(Point(150, 150), Point(250, 250));
    l1.to.y -= 50;
    l1.to.x += 100;

    return 0;
}
