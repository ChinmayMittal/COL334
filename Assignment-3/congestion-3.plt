set terminal png size 1400, 400
set style line 1 lc rgb '#ff0000' lt 1 lw 2 pt 7 ps 0.05
set style line 100 lt 1 lc rgb "gray" lw 2
set style line 101 lt 0.5 lc rgb "gray" lw 1

set output "task-3.png"
set mxtics 5
set title "Congestion Window Size vs Time"
set xlabel "Time (in seconds)"
set ylabel "Congestion Window Size"
set arrow from 20, graph 0 to 20, graph 1 nohead linecolor "blue" 
set arrow from 30, graph 0 to 30, graph 1 nohead linecolor "blue"
set label "UDP transfer started" at 15,300 
set label "UDP Data Rate increased" at 25,1400 

set grid mytics ytics ls 100, ls 101
set grid mxtics xtics ls 100, ls 101

plot "task-3.cwnd" using 1:2 with linespoints ls 1 title "Congestion Window Size"