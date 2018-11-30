import math

def bar_thermometer(current, total, width=80):
    """Return thermometer style progress bar string. `total` argument
    can not be zero. The minimum size of bar returned is 3. Example:

        [..........            ]

    Control and trailing symbols (\r and spaces) are not included.
    See `bar_adaptive` for more information.
    """
    # number of dots on thermometer scale
    avail_dots = width-2
    shaded_dots = int(math.floor(float(current) / total * avail_dots))
    return '[' + '.'*shaded_dots + ' '*(avail_dots-shaded_dots) + ']'

def bar_adaptive(current, total, width=80):
    """Return progress bar string for given values in one of three
    styles depending on available width:

        [..  ] downloaded / total
        downloaded / total
        [.. ]

    if total value is unknown or <= 0, show bytes counter using two
    adaptive styles:

        %s / unknown
        %s

    if there is not enough space on the screen, do not display anything

    returned string doesn't include control characters like \r used to
    place cursor at the beginning of the line to erase previous content.

    this function leaves one free character at the end of string to
    avoid automatic linefeed on Windows.
    """

    # process special case when total size is unknown and return immediately
    if not total or total < 0:
        msg = "%s / unknown" % current
        if len(msg) < width:    # leaves one character to avoid linefeed
            return msg
        if len("%s" % current) < width:
            return "%s" % current

    # --- adaptive layout algorithm ---
    #
    # [x] describe the format of the progress bar
    # [x] describe min width for each data field
    # [x] set priorities for each element
    # [x] select elements to be shown
    #   [x] choose top priority element min_width < avail_width
    #   [x] lessen avail_width by value if min_width
    #   [x] exclude element from priority list and repeat
    
    #  10% [.. ]  10/100
    # pppp bbbbb sssssss

    min_width = {
      'percent': 4,  # 100%
      'bar': 3,      # [.]
      'size': len("%s" % total)*2 + 3, # 'xxxx / yyyy'
    }
    priority = ['percent', 'bar', 'size']

    # select elements to show
    selected = []
    avail = width
    for field in priority:
      if min_width[field] < avail:
        selected.append(field)
        avail -= min_width[field]+1   # +1 is for separator or for reserved space at
                                      # the end of line to avoid linefeed on Windows
    # render
    output = ''
    for field in selected:

      if field == 'percent':
        # fixed size width for percentage
        output += ('%s%%' % (100 * current // total)).rjust(min_width['percent'])
      elif field == 'bar':  # [. ]
        # bar takes its min width + all available space
        output += bar_thermometer(current, total, min_width['bar']+avail)
      elif field == 'size':
        # size field has a constant width (min == max)
        output += ("%s / %s" % (current, total)).rjust(min_width['size'])

      selected = selected[1:]
      if selected:
        output += ' '  # add field separator

    return output