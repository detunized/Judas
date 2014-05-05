struct Point
{
    Point()
        : x(0)
        , y(0)
    {}

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

struct Rectangle
{
    Rectangle(Point left_top, Point right_bottom)
        : left_top(left_top)
        , right_bottom(right_bottom)
    {}

    Point left_top;
    Point right_bottom;
};

struct Bezier
{
    Bezier(Point p1, Point p2, Point p3, Point p4)
    {
        p[0] = p1;
        p[1] = p2;
        p[2] = p3;
        p[3] = p4;
    }

    Point p[4];
};

int main(int argc, char **argv)
{
    Point p1(120, 80);
    p1.x += 90;

    Line l1(Point(270, 140), Point(180, 260));
    Rectangle r1(Point(120, 100), Point(300, 320));
    Bezier b1(Point(120, 100), Point(190, 120), Point(150, 220), Point(300, 320));

    asm("int $3"); // break here (on Intel)

    return 0;
}
