for w in `cut -d ' ' -f 1 first.txt`; do
  echo '         ' $w
  echo $w | sed 's/\(.\)/_\1/g' > input.txt
  ./wordle.py | head -3
done
