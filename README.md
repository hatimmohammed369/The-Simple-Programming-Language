# The-Simple-Programming-Language
A simple programming language

Parts placed inside [] are optional

Each program is divided into (modules), which are basically files
Each file is a module of its own

Primitive data types:
int     =>  Signed/Unsigned integers
real    =>  Real number
string  =>  Anything inside ""
bool    =>  True or False
array   =>  static size single-type-data containers, they hold multiple values of the same type

Variables and Constants:
variable_name: type [ := value [ ; ] ]
const const_name: type [ := value [ ; ] ]

So we can do these things:
x: int := 123;
const y: string = "Hello world!";
const xyz: real = 123.e+234
_zyfe19334: real = -0.3892 + 32.0 * 3344;

This language is indented-blocked
Blocks of code are denoted by their indentation level

Simple I/O:
write(var0, var1, ..., varn)
read(&var0, &var1, ..., &varn)

This &var0 notations is for (references), which are simply actual variables not just values
So things like this are NOT allowed:
read(7);
But this is allowed:
x: int = 0
read(&x)


