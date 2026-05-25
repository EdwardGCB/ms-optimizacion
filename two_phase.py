import simplex as sx
RESTRICTS = []
OPERATORS = []
RESULTS = []
MAIN_L = 0

def operate(up_down, main_eq, restricts, equals, operators):
    global RESTRICTS, OPERATORS, RESULTS, MAIN_L

    RESTRICTS = restricts
    OPERATORS = operators
    RESULTS = equals

    greater, not_greater = reorganize_restrics()

    MAIN_L = len(main_eq)
    sol, cx = phase_one(up_down, greater, not_greater)
    if sol:
        return phase_two(main_eq, up_down)
    else:
        return sol

def phase_one(up_down, greater, not_greater):
    add_vars(greater, not_greater)
    p1_main, cx = add_r(up_down, len(greater))

    if loop(p1_main, cx, up_down, 1):
        return False, 0 # Si no tiene solución
    else:
        return True, cx

def phase_two(main_eq, up_down):
    global RESTRICTS, RESULTS
    p2_eqs()
    cx = main_eq.copy()

    if len(cx) < len(RESTRICTS):
        for i in range(len(RESTRICTS) - len(cx)):
            cx.append(0)

    if len(main_eq) < len(RESTRICTS[0]):
        for i in range(len(RESTRICTS[0]) - len(main_eq)):
            main_eq.append(0)

    paired = sorted(zip(RESTRICTS, RESULTS), key=lambda pair: pair[0].index(1) if 1 in pair[0] else len(pair[0]))

    RESTRICTS, RESULTS = zip(*paired)

    return loop(main_eq, cx, up_down, 2)

def loop(main, cx, up_down, phase):
    global RESTRICTS, RESULTS
    piv_cols = []
    piv_rows = []

    while True:
        zjcj = sx.calc_zjcj(main, RESTRICTS, cx)
        z = sx.calc_z(cx, RESULTS)
        n = [num for num in zjcj if (up_down == 'd' and num > 0) or (up_down == 'u' and num < 0)]

        if not n:
            if z != 0 and phase == 1:
                return True
            else:
                if z == 0 and phase == 2:
                    return True
                return z
        if up_down == 'd':
            piv_col, ind_col = sx.min_pivot_col(main, RESTRICTS, cx, zjcj)
        else:
            piv_col, ind_col = sx.max_pivot_col(main, RESTRICTS, cx, zjcj)
        if ind_col in piv_cols:
            no_sol = True
            break
        piv_cols.append(ind_col)

        ind_row = sx.pivot_row(piv_col, RESULTS)
        if ind_row in piv_rows:
            no_sol = True
            break
        piv_rows.append(ind_row)

        RESTRICTS, RESULTS = sx.gauss_jordan(RESTRICTS, ind_col, ind_row, RESULTS)
        cx[ind_row] = main[ind_col]

def reorganize_restrics():
    global RESTRICTS, OPERATORS, RESULTS

    greater = []
    less = []
    equals = []
    g_indexes = []
    l_indexes = []
    e_indexes = []

    for i in range(len(OPERATORS)):
        oper = OPERATORS[i]
        if oper == '>=':
            greater.append(oper)
            g_indexes.append(i)
        elif oper == '<=':
            less.append(oper)
            l_indexes.append(i)
        else:
            equals.append(oper)
            e_indexes.append(i)

    OPERATORS = greater + equals + less

    greater = [res for i, res in enumerate(RESULTS) if i in g_indexes]
    less = [res for i, res in enumerate(RESULTS) if i in l_indexes]
    equals = [res for i, res in enumerate(RESULTS) if i in e_indexes]

    RESULTS = greater + equals + less

    greater = [res for i, res in enumerate(RESTRICTS) if i in g_indexes]
    less = [res for i, res in enumerate(RESTRICTS) if i in l_indexes]
    equals = [res for i, res in enumerate(RESTRICTS) if i in e_indexes]

    RESTRICTS = greater + equals + less
    not_greater = equals + less

    return greater, not_greater

def add_r(option, greater_length):
    global MAIN_L
    modified_main = [0 for _ in range(MAIN_L + greater_length)]
    cx = []
    ops = [op for op in OPERATORS if op != '<=']
    r_opers = len(ops)
    if option == 'd':
        r = 1
    else:
        r = -1

    for op in range(r_opers):
        modified_main.append(r)
        cx.append(r)

    if len(modified_main) < len(RESTRICTS[0]):
        for i in range(len(RESTRICTS[0]) - len(modified_main)):
            modified_main.append(0)
            cx.append(0)

    return modified_main, cx

def neg_id(greater):
    id_mat = []

    for i in range(len(greater)):
        row = []
        for j in range(len(greater)):
            if i == j:
                row.append(-1)
            else:
                row.append(0)
        id_mat.append(row)

    return id_mat

def add_vars(greater, not_greater):
    global RESTRICTS

    s_i = neg_id(greater)
    r_i = sx.id_matrix(greater)
    gr = s_i + r_i

    rhs_i = sx.id_matrix(not_greater)
    zeros = [0 for _ in range(len(not_greater))]
    rows = [res + s_i[i] + r_i[i] + zeros for i, res in enumerate(greater)]
    zeros = [0 for _ in range(len(gr))]
    rhs_i = [not_greater[i] + zeros + res for i, res in enumerate(rhs_i)]
    rows = rows + rhs_i
    RESTRICTS = rows

def p2_eqs():
    global RESTRICTS, RESULTS, OPERATORS, MAIN_L
    aux = []
    res_aux = []

    for i, x in enumerate(RESTRICTS):
        eq = []
        s = [x for k, x in enumerate(OPERATORS) if x == ">="]
        h = [x for k, x in enumerate(OPERATORS) if x == "<="]
        s_i = len(s)
        h_i = len(h)
        row_len = s_i + MAIN_L

        for j in range(row_len):
            eq.append(x[j])

        end_ind = len(x) - 1

        for k in range(end_ind, end_ind - h_i, -1):
            eq.append(x[k])

        aux.append(eq)
        res_aux.append(RESULTS[i])

    RESTRICTS = aux
    RESULTS = res_aux
