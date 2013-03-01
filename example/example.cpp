#include <iostream>
#include <vector>

// To use:
// CHECK// Python expression to execute on breakpoint (should evaluate to true)
//
// Example:
// CHECK// type(v["watched"]) is dict
#define CHECK (std::cout << ""); // Just some NOOP to set a breakpoint on

using namespace std;

namespace test
{

template <typename T> struct Coord
{
    Coord(T lat = 0, T lon = 0)
        : lat(lat)
        , lon(lon)
    {}

    T lat;
    T lon;
};

typedef Coord<double> DoubleCoord;

class LatLon
{
public:
    LatLon(double lat = 0, double lon = 0)
        : lat(lat)
        , lon(lon)
    {}

    double lat;
    double lon;
};

class Polyline
{
public:
    void add(double lat, double lon)
    {
        points.push_back(LatLon(lat, lon));
    }

    std::vector<LatLon> points;
};

LatLon g_p(52.5237, 13.3037);

void f(LatLon p1 = LatLon(52.5247, 13.4247))
{
    CHECK// v["watches"]["g_p"]["t"] == "test::LatLon"
    CHECK// v["watches"]["g_p"]["n"] == "g_p"
    CHECK// v["watches"]["g_p"]["p"] == [52.5237, 13.3037]

    Polyline line;
    line.add(52.524, 13.423);

    CHECK// v["locals"]["line"]["t"] == "test::Polyline"
    CHECK// v["locals"]["line"]["n"] == "line"
    CHECK// v["locals"]["line"]["p"] == [52.524, 13.423]

    Coord<double> coord(52.524, 13.438);

    CHECK// v["locals"]["coord"]["t"] == "test::Coord<double>"
    CHECK// v["locals"]["coord"]["n"] == "coord"
    CHECK// v["locals"]["coord"]["p"] == [52.524, 13.438]

    DoubleCoord cd(52.539, 13.438);

    CHECK// v["locals"]["cd"]["t"] == "test::DoubleCoord"
    CHECK// v["locals"]["cd"]["n"] == "cd"
    CHECK// v["locals"]["cd"]["p"] == [52.539, 13.438]

    LatLon const const_p1 = p1;
    LatLon &ref = p1;
    LatLon const &const_ref = p1;

    CHECK// v["locals"]["const_p1"]["t"] == "const test::LatLon"
    CHECK// v["locals"]["ref"]["t"] == "test::LatLon &"
    CHECK// v["locals"]["const_ref"]["t"] == "const test::LatLon &"

    LatLon *ptr = &p1;
    LatLon const *const_ptr = &p1;

    CHECK// v["locals"]["ptr"]["t"] == "test::LatLon *"
    CHECK// v["locals"]["const_ptr"]["t"] == "const test::LatLon *"

    int some_int = 0;
    float some_float = some_int + 0.5f;
    char *some_string = "Ahoy, there!";

    CHECK// "some_int" not in v["locals"]
    CHECK// "some_float" not in v["locals"]
    CHECK// "some_string" not in v["locals"]

    for (size_t i = 0; i < 4; ++i)
    {
        line.add(line.points.back().lat + 0.001, line.points.back().lon + 0.0005 * (i + 1));
    }

    CHECK// len(v["locals"]["line"]["p"]) == 10

    for (size_t i = 0; i < line.points.size(); ++i)
    {
        line.points[i].lat += 0.001;
    }

    CHECK// len(v["locals"]["line"]["p"]) == 10

    const LatLon ololo_ololo_ololo(52.52352, 13.42272);

    {
        LatLon p1 = line.points[0];
        LatLon p2 = line.points[1];
        LatLon p3 = line.points[2];
        LatLon p4 = line.points[3];
        LatLon p5 = line.points[4];

        LatLon a(52.5233, 13.4227);
        LatLon b(52.5133, 13.4127);
        LatLon somewhat_longish_variable_name(52.5233, 13.4027);

        a.lat += 0.001;
        a.lat += 0.001;
        a.lat += 0.001;
        a.lat += 0.001;

        CHECK// v["locals"]["p1"]["p"] == v["locals"]["line"]["p"][0:2]
        CHECK// v["locals"]["p2"]["p"] == v["locals"]["line"]["p"][2:4]
        CHECK// v["locals"]["p3"]["p"] == v["locals"]["line"]["p"][4:6]
        CHECK// v["locals"]["p4"]["p"] == v["locals"]["line"]["p"][6:8]
        CHECK// v["locals"]["p5"]["p"] == v["locals"]["line"]["p"][8:10]
        CHECK// v["locals"]["somewhat_longish_variable_name"]["p"] == [52.5233, 13.4027]
    }

    cout << "Hello World!" << endl;
}

}

int main(int argc, char **argv)
{
    test::f();

    return 0;
}
