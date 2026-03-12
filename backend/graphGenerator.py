import uuid
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from matplotlib.colors import LinearSegmentedColormap

reportpath = "/data/agents/runtimereports"
clrlist = ["#deb7a1","#cbbe6b","#a3cf77","#87c04d","#7ed18d","#3ca94f","#92cfd8","#43acbc","#7e99d1","#5679c3"]

async def pieChart(keys, values, title=None, colours=None, donut=None):
    tmpFile = reportpath + "/%s.png" % str(uuid.uuid4())
    keys = keys[:10]
    values = values[:10]
    fig, ax = plt.subplots()
    plt.autoscale(enable=True, tight=True)
    plt.tight_layout()
    colourList = colours if colours else clrlist[:len(keys)]
    ax.pie(values, colors=colourList)
    p = plt.gcf()
    if donut:
        p.gca().add_artist(plt.Circle((0, 0), 0.70, fc='white'))
    ax.legend(["%s - %s" % (k, values[index]) for index, k in enumerate(keys)], bbox_to_anchor=(1, 0, 0.5, 1),
              loc='center left')
    if title:
        plt.title(title, fontsize=16.0, color="#000067", fontweight='bold', pad=1)
    plt.savefig(tmpFile, bbox_inches='tight')
    plt.close()
    return tmpFile


async def horizontalBar(keys, values, title=None, colours=None, figsize=None, valsize=None):
    tmpFile = reportpath + "/%s.png" % str(uuid.uuid4())
    objects = keys[:10]
    width = len(objects) / 50
    if width > 0.6:
        width = 0.6
    performance = values[:10]
    if valsize:
        performance = values[:valsize]
        objects = keys[:valsize]
    y_pos = np.arange(len(objects))
    if figsize:
        fig = plt.figure(figsize=figsize)
    else:
        fig = plt.figure()

    plt.autoscale(enable=True, axis='y', tight=True)
    colourList = colours if colours else clrlist[:len(objects)]
    plt.barh(y_pos, performance, color=colourList, align='center', height=width)
    if figsize:
        plt.yticks(y_pos, objects, horizontalalignment='right')
    else:
        plt.yticks(y_pos, objects, rotation=45, horizontalalignment='right')
    if title:
        plt.title(title, fontsize=16.0, color="#000067", fontweight='bold')
    plt.savefig(tmpFile, bbox_inches='tight')
    plt.close()

    return tmpFile


async def barGraph(keys, values, title=None, colours=None, figsize=None, valsize=None):
    tmpFile = reportpath + "/%s.png" % str(uuid.uuid4())
    objects = keys[:10]
    width = len(objects) / 50
    if width > 0.6:
        width = 0.6
    performance = values[:10]
    if valsize:
        performance = values[:valsize]
        objects = keys[:valsize]
    y_pos = np.arange(len(objects))
    if figsize:
        fig = plt.figure(figsize=figsize)
    else:
        fig = plt.figure()
    plt.autoscale(enable=True, axis='y')
    colourList = colours if colours else clrlist[:len(objects)]
    plt.bar(objects, performance, color=colourList, align='center', width=width)

    if figsize:
        plt.xticks(y_pos, objects, horizontalalignment='right')
    else:
        plt.xticks(y_pos, objects, rotation=45, horizontalalignment='right')
    if title:
        plt.title(title, fontsize=16.0, color="#000067", fontweight='bold', pad=1)
    plt.savefig(tmpFile, bbox_inches='tight')
    plt.close()
    return tmpFile


async def lineGraph(labels, values, title=None, colours=None):
    tmpFile = reportpath + "/%s.png" % str(uuid.uuid4())
    labels = labels[:10]
    values = values[:10]
    fig, ax = plt.subplots()
    plt.autoscale(enable=True, tight=True)
    plt.tight_layout()
    if isinstance(colours,str):
        plt.plot(labels, values, linestyle='-', color=colours)
    else:
        plt.plot(labels, values, linestyle='-')

    p = plt.gcf()
    if title:
        plt.title(title, fontsize=16.0, color="#000067", fontweight='bold', pad=1)
    y_pos = np.arange(len(labels))
    plt.xticks(y_pos, labels, rotation=45, horizontalalignment='right')
    plt.savefig(tmpFile, bbox_inches='tight')
    plt.close()
    return tmpFile


async def stemGraph(labels, values, title=None, colours=None):
    tmpFile = reportpath + "/%s.png" % str(uuid.uuid4())
    labels = labels[:10]
    values = values[:10]
    fig, ax = plt.subplots()
    plt.autoscale(enable=True, tight=True)
    plt.tight_layout()
    if isinstance(colours,str):
        plt.stem(labels, values, use_line_collection=True, linefmt=colours)
    else:
        plt.stem(labels, values, use_line_collection=True)

    p = plt.gcf()
    if title:
        plt.title(title, fontsize=16.0, color="#000067", fontweight='bold', pad=1)
    y_pos = np.arange(len(labels))
    plt.xticks(y_pos, labels, rotation=45, horizontalalignment='right')
    plt.savefig(tmpFile, bbox_inches='tight')
    plt.close()
    return tmpFile


async def areaPlot(labels, values, title=None, colours=None):
    tmpFile = reportpath + "/%s.png" % str(uuid.uuid4())
    labels = labels[:10]
    values = values[:10]
    fig, ax = plt.subplots()
    plt.autoscale(enable=True, tight=True)
    plt.tight_layout()
    if isinstance(colours,str):
        plt.fill_between(labels, values, color=colours)
    else:
        plt.fill_between(labels, values)
    p = plt.gcf()
    if title:
        plt.title(title, fontsize=16.0, color="#000067", fontweight='bold', pad=1)
    y_pos = np.arange(len(labels))
    plt.xticks(y_pos, labels, rotation=45, horizontalalignment='right')
    plt.savefig(tmpFile, bbox_inches='tight')
    plt.close()
    return tmpFile


async def barVsLine(barval, lineval, labels, figsize=None):
    tmpFile = reportpath + "/%s.png" % str(uuid.uuid4())
    fig, ax = plt.subplots()
    y_pos = np.arange(len(labels))
    plt.ylabel(barval["Name"])
    plt.bar(y_pos, barval["values"], color="#d1ecff")
    ax1 = ax.twinx()
    plt.plot(y_pos, lineval["values"], marker='s', color="#eba63d")
    plt.ylabel(lineval["Name"])
    plt.xticks(y_pos, labels)
    fig.autofmt_xdate(rotation=45)
    plt.locator_params(axis='x', nbins=10)
    plt.savefig(tmpFile, bbox_inches='tight')
    plt.close()
    return tmpFile


async def areaStack(title, rangeval, values, labels, colours):
    tmpFile = reportpath + "/%s.png" % str(uuid.uuid4())
    fig = plt.figure(figsize=(10, 5))
    fig.suptitle(title, fontsize=16.0, color="#000067", fontweight='bold')
    plt.stackplot(rangeval, values, labels=labels,
                  colors=colours)
    plt.legend(loc='upper left')
    plt.xticks(rangeval)
    fig.autofmt_xdate(rotation=45)
    plt.locator_params(axis='x', nbins=10)
    plt.savefig(tmpFile, bbox_inches='tight')
    plt.close()
    return tmpFile


async def lineStack(title, rangeval, values, labels, colours):
    tmpFile = reportpath + "/%s.png" % str(uuid.uuid4())
    fig = plt.figure(figsize=(10, 5))
    fig.suptitle(title, fontsize=16.0, color="#000067", fontweight='bold')
    loop = 0
    for lineplot in labels:
        plt.plot(rangeval, values[loop], label=labels[loop],
                 color=colours[loop])
        loop += 1
    plt.legend(loc='upper left')
    plt.xticks(rangeval)
    fig.autofmt_xdate(rotation=45)
    plt.locator_params(axis='x', nbins=10)
    plt.savefig(tmpFile, bbox_inches='tight')
    plt.close()
    return tmpFile


async def multiBargrah(title, rangeval, labels, colour, values):
    tmpFile = reportpath + "/%s.png" % str(uuid.uuid4())
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.suptitle(title, fontsize=16.0, color="#000067", fontweight='bold')
    y_pos = np.arange(len(rangeval))
    if len(labels) % 2 == 0:
        valrange = [i for i in list(range(int(-len(labels) / 2), int(len(labels) / 2) + 1)) if
                    i != 0]
    else:
        valrange = list(
            range(int(-len(labels) / 2), int(len(labels) / 2) + 1))
    width = len(rangeval) / 50
    if width > 0.5:
        width = 0.5
    rectshbar = {}
    loopidx = 0
    for val in valrange:
        addval = 0
        if abs(val) != 1:
            addval = ((width / 2) * val) / 2
        rectshbar["rectshbar" + str(loopidx)] = ax.bar(y_pos + addval + (width / 2) * val,
                                                       values[loopidx], width,
                                                       label=labels[loopidx],
                                                       color=colour[loopidx])
        loopidx += 1
    plt.xticks(y_pos, rangeval)
    ax.set_ylabel("Count")
    fig.autofmt_xdate(rotation=45)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.legend()
    plt.savefig(tmpFile, bbox_inches='tight')
    return tmpFile


async def heatMap(title, data, colRange=None):
    tmpFile = reportpath + "/%s.png" % str(uuid.uuid4())
    fig, ax = plt.subplots(sharex=True, figsize=(8, 5))
    if colRange:
        cmap = LinearSegmentedColormap.from_list('rg', colRange)
    else:
        cmap = LinearSegmentedColormap.from_list('rg', clrlist)
    ax.imshow(np.array([np.arange(data[2], data[3]) for i in range(0, int(data[3] * 5 / 100))]), cmap=cmap)
    for spine in ['bottom', 'top', 'right', 'left']:
        ax.spines[spine].set_visible(False)
    ax.set(xlabel=data[0])
    plt.setp(ax.get_xticklabels(), visible=False)
    plt.setp(ax.get_yticklabels(), visible=False)
    ax.tick_params(axis='both', which='both', length=0)
    ymin, ymax = ax.get_ylim()
    ax.vlines(data[1], ymin + 1, ymax - 1, linewidth=2, color="black", clip_on=False)
    fig.suptitle(title, fontsize=22)
    plt.savefig(tmpFile, bbox_inches='tight')
    plt.close()
    return tmpFile

