def direction(degrees, numeric=True):
    intervals = [22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5]
    if numeric:
        interval_name = [1, 2, 3, 4, 5, 6, 7, 8]
    else:
        interval_name = ['N', 'NØ', 'Ø', 'SØ', 'S', 'SV', 'V', 'NV']
    for i in range(0,len(intervals)-1):
        if intervals[i] <= degrees < intervals[i+1]:
            return interval_name[i+1]
    return interval_name[0]