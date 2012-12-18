#include <iostream>
#include <vector>

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
    Polyline line;
    line.add(52.524, 13.423);

    Coord<double> coord(52.524, 13.438);
    DoubleCoord cd(52.539, 13.438);

    int some_int = 0;
    float some_float = some_int + 0.5f;
    char *some_string = "Ahoy, there!";

    for (size_t i = 0; i < 4; ++i)
    {
        line.add(line.points.back().lat + 0.001, line.points.back().lon + 0.0005 * (i + 1));
    }

    for (size_t i = 0; i < line.points.size(); ++i)
    {
        line.points[i].lat += 0.001;
    }

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
    }

    cout << "Hello World!" << endl;
}

}

int main(int argc, char **argv)
{
    test::f();
    return 0;
}
