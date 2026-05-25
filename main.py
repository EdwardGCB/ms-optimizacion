# Press Ctrl+F5 to execute script
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
# Press F9 to toggle the breakpoint.
# Press the green button in the gutter to run the script.
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
import simplex as sx
import two_phase as tp

if __name__ == '__main__':
    up_down = 'd' # Max (u) or min (d)
    main_eq = [4, 1]
    restricts = [[3, 1], [4, 3], [1, 2]]
    operators = ['=', '>=', '<=']
    equals = [3, 6, 4]

    # main_eq = [5, 4]
    # restricts = [[6, 4], [1, 2], [0, 1], [-1, 1], [5, 8], [1, 8]]
    # operators = ['>=', '<=', '==', '>=', '<=', '>=']
    # equals = [24, 6, 2, 1, 8, 5, 10]

    tp.operate(up_down, main_eq, restricts, equals, operators)
    # tp.operate(up_down, main_eq, restricts, equals)
    # returned = sx.simplex(up_down, main_eq, restricts, equals)
    # print(f"{returned[1]}Z = {returned[0]}")
