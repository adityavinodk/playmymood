import matplotlib.pyplot as plt
import numpy as np

P1 = np.array([2.5, 2, 3])
P2 = np.array([2, 1.5, 1])
P3 = np.array([3.5, 3, 3.5])
P4 = np.array([1.5, 1, 1.5])

points = ["P1", "P2", "P3", "P4"]
x_pos = np.arange(len(points))
cte = [np.mean(P1), np.mean(P2), np.mean(P3), np.mean(P4)]
error = [np.std(P1), np.std(P2), np.std(P3), np.std(P4)]

fig, ax = plt.subplots()
ax.bar(points, cte, yerr=error, align="center", alpha=0.5, ecolor="black", capsize=10)
ax.set_ylabel("Average rating")
ax.set_xticks(x_pos)
ax.set_xticklabels(points)
ax.set_title("Average Ratings given to recommendations of different parameters")
ax.yaxis.grid(True)

# Save the figure and show
plt.tight_layout()
plt.savefig("bar_plot_with_error_bars.png")
plt.show()
