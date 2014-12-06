for i in 0,0 10,10 11,5 17,6 16,4 19,18 17,3 18,2; do
IFS=",";
set $i;

f_fn1="forwardnodes_$1_$2_independent.csv";
f_fn2="forwardnodes_$1_$2_minkey_warmstart.csv";

b_fn1="backwardnodes_$1_$2_independent.csv";
b_fn2="backwardnodes_$1_$2_minkey_warmstart.csv";

if diff -q $f_fn1 $f_fn2 > /dev/null; then
echo -e "$f_fn1 \t $f_fn2 \t\t SAME";
else
echo "DIFFERENCE FOUND IN $f_fn1 and $f_fn2"
fi
if diff -q $b_fn1 $b_fn2 > /dev/null; then
echo -e "$b_fn1 \t $b_fn2 \t\t SAME";
else
echo "DIFFERENCE FOUND IN $b_fn1 and $b_fn2"
fi
done