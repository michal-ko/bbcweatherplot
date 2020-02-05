from bs4 import BeautifulSoup
import requests
import re
import datetime
import matplotlib.pyplot as plt
import os
import subprocess
from scipy.ndimage.filters import gaussian_filter1d


def get_weather_data(bbc_weather_url):

    now = datetime.datetime.now()
    all_results = list()

    try:
        source = requests.get(bbc_weather_url).text
    except Exception as e:
        print(f"Upss, couldn't connect to {bbc_weather_url}", e)
        return -1
    soup = BeautifulSoup(source, 'lxml')

    objList = soup.find_all('li', class_="wr-time-slot wr-js-time-slot")

    for obj in objList:

        results = {
            'time': None,
            'temperature': None,
            'cop': None,
            'humidity': None,
            'pressure': None
        }

        time_ = obj.find('span', class_="wr-time-slot-primary__time").text
        time_ = datetime.datetime.strptime(time_, '%H:%M')
        time_ = time_.replace(year=now.year, month=now.month, day=now.day)
        temp_ = obj.find('span', class_="wr-value--temperature--c").text[:-1]
        chance_of_precipitation_ = obj.find('div', class_="wr-u-font-weight-500").text[:-24]
        atmos_data = obj.find('dl', class_="wr-time-slot-secondary__list").text
        humidity_ = re.search(r'Humidity(\d+)', atmos_data).group(1)
        pressure_ = re.search(r'Pressure(\d+)', atmos_data).group(1)

        results['time'] = time_
        results['temperature'] = temp_
        results['cop'] = chance_of_precipitation_
        results['humidity'] = humidity_
        results['pressure'] = pressure_
        all_results.append(results)

    # fix dates
    for obj in all_results:
        if obj['time'] < all_results[0]['time']:
            obj['time'] += datetime.timedelta(days=1)

    # add timestamp when data collected
    all_results.append({'check_time': datetime.datetime.timestamp(now).__int__()})
    return all_results


def plot_data(data_dict):

    x_vals = list()  # time
    y_temp = list()  # temperature
    y_cop = list()  # chance of precipitation
    y_hum = list()  # humidity
    y_press = list()  # pressure

    # re-shuffle data to lists
    for obj in data_dict[:-1]:
        x_vals.append(obj['time'].strftime('%H:%M'))
        y_temp.append(int(obj['temperature']))
        y_cop.append(int(obj['cop']))
        y_hum.append(int(obj['humidity']))
        y_press.append(int(obj['pressure'])/10)

    fig, ax = plt.subplots(figsize=(16, 4))
    plt.xlabel('London, UK')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.plot(x_vals, y_temp, label='temperature[°C]', color='green', marker='o', markerfacecolor='green', markersize=3)

    # ax.plot(x_vals, gaussian_filter1d(y_cop, sigma=2), label='chance of precip.[%]')  # smoothed y_cop
    ax.plot(x_vals, y_cop, label='chance of precip.[%]')
    ax.plot(x_vals, y_hum, label='humidity[%]')
    ax.plot(x_vals, y_press, label='pressure[mb]')

    # show temperature labels on the graph
    for idx, t in enumerate(y_temp):
        plt.text(x_vals[idx], y_temp[idx], f"{t}°C", fontsize=9)

    # show pressure labels on the graph
    for idx, p in enumerate(y_press):
        plt.text(x_vals[idx], y_press[idx], f"{int(p*10)}", fontsize=9)

    ax.legend()
    ax.grid(True, color='grey', linestyle='-', linewidth=0.25, alpha=0.5)

    # save graph to PNG
    file_name= f"london_weather-{datetime.datetime.fromtimestamp(data_dict[-1]['check_time']).strftime('%Y-%m-%d')}.png"
    plt.savefig(file_name, dpi=150, transparent=True)
    plt.close()

    return f"{os.getcwd()}/{file_name}"


def get_screen_res():
    cmd = ['xrandr']
    cmd2 = ['grep', '*']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, encoding='utf-8')
    p2 = subprocess.Popen(cmd2, stdin=p.stdout, stdout=subprocess.PIPE, encoding='utf-8')
    p.stdout.close()

    resolution_string, junk = p2.communicate()
    resolution = resolution_string.split()[0]
    return tuple(resolution.split('x'))


def get_curr_wallpaper():
    bash_cmd = "gsettings get org.gnome.desktop.background picture-uri"
    curr_path = subprocess.run(bash_cmd.split(), stdout=subprocess.PIPE, encoding='utf-8').stdout
    return curr_path[8:-2]  # remove 'file//' and ' at the end


def set_wallpaper(path_to_pic):
    bash_cmd = f"gsettings set org.gnome.desktop.background picture-uri \"{path_to_pic}\""
    run = subprocess.run(bash_cmd.split(), stderr=subprocess.PIPE).stderr
    if len(run) > 0:
        print(run)
    return


if __name__ == "__main__":
    data = get_weather_data("https://www.bbc.co.uk/weather/2643743")
    new_pic_path = plot_data(data)
    print(get_screen_res())
