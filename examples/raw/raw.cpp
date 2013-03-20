int main(int argc, char **argv)
{
    int integer = 0;
    integer += 10;
    integer += 20;
    integer += 30;
    integer += 40;

    char const *string = "Beep, beep.";
    string = "Pew pew";

    asm("int $3"); // break here (on Intel)

    return 0;
}
