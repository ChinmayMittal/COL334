connection = "connection-1"
protocol = "TcpNewRenoPlus"
file = connection."-".protocol.".cwnd"

reset
set term wxt enhanced
set terminal png size 1200, 400
set style line 1 lc rgb '#ff0000' lt 1 lw 2 pt 7 ps 0.05
set style line 100 lt 1 lc rgb "gray" lw 2
set style line 101 lt 0.5 lc rgb "gray" lw 1

set xrange [ 1 : 30 ]

set output connection."-".protocol.".png"
set mxtics 5
set title "Congestion Window Size vs Time for ".connection." with congestion control using ".protocol
set xlabel "Time (in seconds)"
set ylabel "Congestion Window Size"

set grid mytics ytics ls 100, ls 101
set grid mxtics xtics ls 100, ls 101

plot file using 1:2 with linespoints ls 1 title "Congestion Window Size"