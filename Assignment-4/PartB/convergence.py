import matplotlib.pyplot as plt

file = "ass-4-b.1.4"
dat_file = file +  ".txt"
png_file = file + ".png"

with open(dat_file) as f:
    for line in f.readlines():
        values = line.split()
        x = float(values[0])
        y = float(values[1])
        plt.plot([x], [y], marker="X", markersize=10, markerfacecolor = "red", markeredgecolor = "red")
        plt.grid()
        plt.ylabel("All routing tables converged")
        plt.xlabel("Time in seconds")
        plt.title("Convergence of routing table of all routers with time")
    plt.savefig(png_file)
    plt.show()