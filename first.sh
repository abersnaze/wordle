for w in `cut -d ' ' -f 1 first.txt`; do
  if [ ! -f output/$w.txt ]; then
    echo $w
    ./wordle.py $w | tee output/$w.tmp
    if [ $? == 0 ]; then
      mv output/$w.tmp output/$w.txt
    fi
    sleep 10
  fi
done
