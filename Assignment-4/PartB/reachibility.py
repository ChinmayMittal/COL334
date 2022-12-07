import matplotlib.pyplot as plt

file = "ass-4-b.3"
dat_file = file +  ".txt"
png_file = file + ".png"
i = 0 
with open(dat_file) as f:
    for line in f.readlines():
        values = line.split()
        x = float(values[0])
        y = float(values[1])
        plt.grid(b=True)
        plt.plot([x], [y], marker="X", markersize=10, markerfacecolor = "red", markeredgecolor = "red")
        # if( i% 2 == 0 ):
        #     plt.text(x+1,0.7, f'{x}s' )
        # else:
        #     plt.text(x+1,0.3, f'{x}s' )
        # i += 1

        # plt.axvline(x)
        # plt.text(x, 0.5)
        plt.ylabel("Destination is Reachable from source")
        plt.xlabel("Time in seconds")
        plt.title("Source To Destination Reachibility with Time")
    plt.savefig(png_file)
    plt.show()