import numpy as np
import matplotlib.pyplot as plt

bounds = np.array([[1, 201]])
number_of_initial_points = 8

thread_pool_max = 200
thread_pool_min = 1

data = []
x_data = []
y_data = [-0.39733866,-8.41470985,-17.78692088,41.87049125]

param_history = [2,10,22,44]

next_x = 2

def function(X):
    #return np.sin(X / 5.0) * X
    return -1.0*np.sin(X/10.0)*X

def initial_plot():
    global X_plot_data
    X_plot_data = np.arange(bounds[:, 0], bounds[:, 1], 1).reshape(-1, 1)
    global Y_plot_data
    Y_plot_data = function(X_plot_data)

    plt.plot(X_plot_data, Y_plot_data, lw=2, label='Noise-free objective')
    # plt.plot([2], [4], 'kx', mew=3, label='Noisy samples')
    plt.legend()
    # plt.axvline(x=2, ls='--', c='k', lw=1)
    plt.show()

noise_dist = np.random.normal(0, 5, 20)
# initial_plot()

def get_initial_points():
    for i in range(0, (number_of_initial_points+1)):
        x = thread_pool_min + i * (thread_pool_max - thread_pool_min) / number_of_initial_points
        x = int(x)
        print('X = %i', x)
        x_data.append([x])
        y_data.append(get_performance([x], thread_pool_min, i, online))
        param_history.append([x])

def get_performance(x_pass, lower_bound, loc, online_check):
    global data

    noise_loc = np.random.randint(0, 19)
    x_data_loc = np.where(X_plot_data == x_pass)
    return_val = Y_plot_data[x_data_loc] + noise_dist[noise_loc]
    #return_val = Y_plot_data[x_data_loc]
    return return_val

def data_plot():
    # plot_approximation( param_history, y_data, next_x, show_legend=i == 0)
    plot_approximation(param_history, y_data, next_x, True)
    # plt.title(f'Iteration {i + 1}')
    plt.show(block=False)
    plt.pause(0.5)
    plt.close()

def plot_approximation( X_sample, Y_sample, X_next=None, show_legend=False):
    global X_plot_data
    X_plot_data = np.arange(bounds[:, 0], bounds[:, 1], 1).reshape(-1, 1)
    global Y_plot_data
    Y_plot_data = function(X_plot_data)
    plt.plot(X_plot_data, Y_plot_data, lw=2, label='Noise-free objective')
    plt.plot(X_sample, Y_sample, 'kx', mew=3, label='Noisy samples')
    if X_next:
        plt.axvline(x=X_next, ls='--', c='k', lw=1)
    if show_legend:
        plt.legend()

data_plot()
