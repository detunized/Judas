#include <iostream>
#include <vector>

using namespace std;

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
    Polyline(size_t count)
        : count(count)
        , points(new LatLon[count])
    {}

    size_t count;
    LatLon *points;
};

void f(LatLon p1 = LatLon(52.5247, 13.4237))
{
    Polyline line(5);
    line.points[0].lat = 52.524;
    line.points[0].lon = 13.423;

    for (size_t i = 1; i < line.count; ++i)
    {
        line.points[i].lat = line.points[i - 1].lat + 0.001;
        line.points[i].lon = line.points[i - 1].lon + 0.0005 * i;
    }

    for (size_t i = 0; i < line.count; ++i)
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

int main(int argc, char **argv)
{
    f();
    return 0;
}
