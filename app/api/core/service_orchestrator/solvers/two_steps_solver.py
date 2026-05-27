from typing import List, Optional, Tuple

from app.common.models.optimization import (
    Iteration,
    PhaseOneRestriction,
    PhaseOneSetup,
    PhaseTwoSetup,
    PivotInfo,
    RowOperation,
    TableRow,
    TwoPhaseResult,
)

EPS = 1e-9
MAX_ITERATIONS = 200


class TwoPhaseSolver:
    """
    Resuelve un problema de programación lineal por el método de las dos fases.

    Para cada iteración registra:
      - La tabla simplex (Cj, base, A, bi).
      - La fila Zj-Cj y el valor de z.
      - Cómo se eligió la columna y la fila pivote (con explicación textual).
      - Las operaciones de fila que producirán la siguiente tabla
        (formato "F5 = F1 · 1/6", "F6 = F2 - 4 · F5", etc.).
    """

    def __init__(self, payload):
        self.sense: str = payload.optimization.value
        self.original_c: List[float] = [float(x) for x in payload.coefficients]
        self.restrictions = payload.restrictions
        self.n_vars: int = payload.nro_variables

        self.var_names: List[str] = []
        self.A: List[List[float]] = []
        self.b: List[float] = []
        self.basis: List[int] = []
        self.artificials: List[int] = []

        self.iterations: List[Iteration] = []
        self.row_counter: int = 0
        self.row_labels: List[str] = []
        self.phase_one_setup: Optional[PhaseOneSetup] = None
        self.phase_two_setup: Optional[PhaseTwoSetup] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def solve(self) -> dict:
        self._build_standard_form()

        feasible = self._phase_one()
        if not feasible:
            return TwoPhaseResult(
                status="infeasible",
                z=None,
                basis=[self.var_names[i] for i in self.basis],
                solution={},
                phase_one_setup=self.phase_one_setup,
                iterations=self.iterations,
            ).model_dump()

        bounded = self._phase_two()
        if not bounded:
            return TwoPhaseResult(
                status="unbounded",
                z=None,
                basis=[self.var_names[i] for i in self.basis],
                solution={},
                phase_one_setup=self.phase_one_setup,
                phase_two_setup=self.phase_two_setup,
                iterations=self.iterations,
            ).model_dump()

        return self._final_result()

    # ------------------------------------------------------------------
    # Forma estándar
    # ------------------------------------------------------------------
    def _build_standard_form(self) -> None:
        for i in range(self.n_vars):
            self.var_names.append(f"X{i + 1}")

        normalized = []
        for r in self.restrictions:
            coefs = [float(x) for x in r.coefficients]
            bval = float(r.value)
            op = r.operator.value
            if bval < 0:
                coefs = [-c for c in coefs]
                bval = -bval
                if op == "<=":
                    op = ">="
                elif op == ">=":
                    op = "<="
            normalized.append((op, coefs, bval))

        n_h = sum(1 for op, _, _ in normalized if op == "<=")
        n_s = sum(1 for op, _, _ in normalized if op == ">=")
        n_r = sum(1 for op, _, _ in normalized if op in (">=", "="))

        h_offset = self.n_vars
        s_offset = h_offset + n_h
        r_offset = s_offset + n_s

        for i in range(n_h):
            self.var_names.append(f"H{i + 1}")
        for i in range(n_s):
            self.var_names.append(f"S{i + 1}")
        for i in range(n_r):
            self.var_names.append(f"R{i + 1}")
            self.artificials.append(r_offset + i)

        h_count = 0
        s_count = 0
        r_count = 0
        phase_one_restrictions: List[PhaseOneRestriction] = []

        for op, coefs, bval in normalized:
            row = coefs + [0.0] * (n_h + n_s + n_r)
            added_vars: List[str] = []

            if op == "<=":
                col = h_offset + h_count
                row[col] = 1.0
                self.basis.append(col)
                added_vars.append(self.var_names[col])
                h_count += 1
            elif op == ">=":
                s_col = s_offset + s_count
                r_col = r_offset + r_count
                row[s_col] = -1.0
                row[r_col] = 1.0
                self.basis.append(r_col)
                added_vars.extend([self.var_names[s_col], self.var_names[r_col]])
                s_count += 1
                r_count += 1
            else:
                r_col = r_offset + r_count
                row[r_col] = 1.0
                self.basis.append(r_col)
                added_vars.append(self.var_names[r_col])
                r_count += 1

            self.A.append(row)
            self.b.append(bval)

            phase_one_restrictions.append(
                PhaseOneRestriction(
                    original_operator=op,
                    operator="=",
                    coefficients=list(row),
                    bi=bval,
                    added_vars=added_vars,
                    text=self._format_equation(row, bval),
                )
            )

        self.row_labels = [self._new_row_label() for _ in self.A]

        artificial_names = [self.var_names[i] for i in self.artificials]
        if artificial_names:
            objective_text = "MIN z = " + " + ".join(artificial_names)
        else:
            objective_text = "MIN z = 0 (no se requieren variables artificiales)"

        objective_coefficients = [0.0] * len(self.var_names)
        for idx in self.artificials:
            objective_coefficients[idx] = 1.0

        self.phase_one_setup = PhaseOneSetup(
            objective_text=objective_text,
            objective_coefficients=objective_coefficients,
            variables=list(self.var_names),
            restrictions=phase_one_restrictions,
        )

    def _format_equation(
        self,
        coefficients: List[float],
        bi: float,
        var_names: Optional[List[str]] = None,
    ) -> str:
        names = var_names or self.var_names
        parts: List[str] = []
        for j, coef in enumerate(coefficients):
            if abs(coef) < EPS:
                continue
            name = names[j]
            if coef == 1:
                term = f"+ {name}"
            elif coef == -1:
                term = f"- {name}"
            elif coef > 0:
                term = f"+ {self._fmt(coef)}{name}"
            else:
                term = f"- {self._fmt(abs(coef))}{name}"
            if not parts and term.startswith("+ "):
                term = term[2:]
            parts.append(term)
        left = " ".join(parts) if parts else "0"
        return f"{left} = {self._fmt(bi)}"

    def _format_objective(
        self,
        coefficients: List[float],
        var_names: List[str],
        sense: str,
    ) -> str:
        parts: List[str] = []
        for j, coef in enumerate(coefficients):
            if abs(coef) < EPS:
                continue
            name = var_names[j]
            if coef == 1:
                term = f"+ {name}"
            elif coef == -1:
                term = f"- {name}"
            elif coef > 0:
                term = f"+ {self._fmt(coef)}{name}"
            else:
                term = f"- {self._fmt(abs(coef))}{name}"
            if not parts and term.startswith("+ "):
                term = term[2:]
            parts.append(term)
        left = " ".join(parts) if parts else "0"
        return f"{sense} z = {left}"

    def _new_row_label(self) -> str:
        self.row_counter += 1
        return f"F{self.row_counter}"

    # ------------------------------------------------------------------
    # Cálculos de la tabla
    # ------------------------------------------------------------------
    def _compute_zj_cj(self, cj: List[float]) -> Tuple[List[float], float]:
        cb = [cj[i] for i in self.basis]
        n_cols = len(cj)
        zj_cj: List[float] = []
        for j in range(n_cols):
            zj = sum(cb[i] * self.A[i][j] for i in range(len(self.basis)))
            zj_cj.append(zj - cj[j])
        z = sum(cb[i] * self.b[i] for i in range(len(self.basis)))
        return zj_cj, z

    def _choose_pivot_column(
        self,
        zj_cj: List[float],
        allowed_cols: List[int],
        sense: str,
    ) -> Tuple[Optional[int], str]:
        if not allowed_cols:
            return None, "No hay columnas candidatas"

        if sense == "MAX":
            best = min(allowed_cols, key=lambda j: zj_cj[j])
            if zj_cj[best] >= -EPS:
                return None, "Todos los Zj-Cj son no negativos: óptimo alcanzado"
            reason = (
                f"Zj-Cj más negativo en {self.var_names[best]}: "
                f"{self._fmt(zj_cj[best])}"
            )
            return best, reason

        best = max(allowed_cols, key=lambda j: zj_cj[j])
        if zj_cj[best] <= EPS:
            return None, "Todos los Zj-Cj son no positivos: óptimo alcanzado"
        reason = (
            f"Zj-Cj más positivo en {self.var_names[best]}: "
            f"{self._fmt(zj_cj[best])}"
        )
        return best, reason

    def _choose_pivot_row(self, col: int) -> Tuple[Optional[int], str]:
        best_i = -1
        best_ratio: Optional[float] = None
        ratios: List[str] = []

        for i, row in enumerate(self.A):
            if row[col] > EPS:
                ratio = self.b[i] / row[col]
                ratios.append(
                    f"{self.row_labels[i]}: {self._fmt(self.b[i])}/"
                    f"{self._fmt(row[col])} = {self._fmt(ratio)}"
                )
                if best_ratio is None or ratio < best_ratio - EPS:
                    best_ratio = ratio
                    best_i = i

        if best_i < 0:
            return None, (
                "No hay coeficientes positivos en la columna pivote: "
                "el problema es no acotado"
            )

        reason = (
            f"Menor cociente bi/aij positivo: "
            f"{self._fmt(self.b[best_i])}/{self._fmt(self.A[best_i][col])} = "
            f"{self._fmt(best_ratio)} en {self.row_labels[best_i]}. "
            f"Comparados: {'; '.join(ratios)}"
        )
        return best_i, reason

    # ------------------------------------------------------------------
    # Gauss-Jordan sobre el pivote
    # ------------------------------------------------------------------
    def _pivot(self, row: int, col: int) -> List[RowOperation]:
        pivot_val = self.A[row][col]
        old_labels = list(self.row_labels)
        ops: List[RowOperation] = []

        new_pivot_row = [x / pivot_val for x in self.A[row]]
        new_pivot_b = self.b[row] / pivot_val
        self.A[row] = new_pivot_row
        self.b[row] = new_pivot_b

        new_label = self._new_row_label()
        ops.append(
            RowOperation(
                target=new_label,
                expression=f"{old_labels[row]} · (1/{self._fmt(pivot_val)})",
                factor=1.0 / pivot_val,
                source_rows=[old_labels[row]],
            )
        )
        self.row_labels[row] = new_label

        for i in range(len(self.A)):
            if i == row:
                continue
            factor = self.A[i][col]
            if abs(factor) < EPS:
                continue

            self.A[i] = [
                self.A[i][j] - factor * new_pivot_row[j]
                for j in range(len(new_pivot_row))
            ]
            self.b[i] = self.b[i] - factor * new_pivot_b

            target = self._new_row_label()
            sign = "-" if factor > 0 else "+"
            ops.append(
                RowOperation(
                    target=target,
                    expression=(
                        f"{old_labels[i]} {sign} {self._fmt(abs(factor))} · {new_label}"
                    ),
                    factor=-factor,
                    source_rows=[old_labels[i], new_label],
                )
            )
            self.row_labels[i] = target

        self.basis[row] = col
        return ops

    # ------------------------------------------------------------------
    # Fases
    # ------------------------------------------------------------------
    def _phase_one(self) -> bool:
        if not self.artificials:
            return True

        cj = [0.0] * len(self.var_names)
        for idx in self.artificials:
            cj[idx] = 1.0

        allowed_cols = list(range(len(self.var_names)))
        completed = self._run_phase(cj, allowed_cols, sense="MIN", phase=1)
        if not completed:
            return False

        _, z = self._compute_zj_cj(cj)
        return abs(z) < EPS

    def _phase_two(self) -> bool:
        self._build_phase_two_setup()
        self._strip_artificial_columns()

        cj = [0.0] * len(self.var_names)
        for i in range(self.n_vars):
            cj[i] = self.original_c[i]

        allowed_cols = list(range(len(self.var_names)))
        return self._run_phase(cj, allowed_cols, sense=self.sense, phase=2)

    def _build_phase_two_setup(self) -> None:
        kept_indices = [
            j for j in range(len(self.var_names)) if j not in self.artificials
        ]
        kept_names = [self.var_names[j] for j in kept_indices]
        removed_names = [self.var_names[j] for j in self.artificials]

        objective_coefficients = [0.0] * len(kept_names)
        for i in range(self.n_vars):
            if i in kept_indices:
                new_idx = kept_indices.index(i)
                objective_coefficients[new_idx] = self.original_c[i]

        restrictions: List[PhaseOneRestriction] = []
        for i, row in enumerate(self.A):
            sliced = [row[j] for j in kept_indices]
            added_vars = [
                kept_names[j]
                for j, coef in enumerate(sliced)
                if abs(coef) > EPS and kept_names[j].startswith(("H", "S"))
            ]
            restrictions.append(
                PhaseOneRestriction(
                    original_operator="=",
                    operator="=",
                    coefficients=[float(x) for x in sliced],
                    bi=float(self.b[i]),
                    added_vars=added_vars,
                    text=self._format_equation(sliced, self.b[i], kept_names),
                )
            )

        self.phase_two_setup = PhaseTwoSetup(
            objective_text=self._format_objective(
                objective_coefficients, kept_names, self.sense
            ),
            objective_coefficients=[float(x) for x in objective_coefficients],
            variables=kept_names,
            removed_variables=removed_names,
            restrictions=restrictions,
            initial_basis=[self.var_names[b] for b in self.basis],
        )

    def _strip_artificial_columns(self) -> None:
        if not self.artificials:
            return

        kept_indices = [
            j for j in range(len(self.var_names)) if j not in self.artificials
        ]
        old_to_new = {old: new for new, old in enumerate(kept_indices)}

        self.A = [[row[j] for j in kept_indices] for row in self.A]
        self.var_names = [self.var_names[j] for j in kept_indices]
        self.basis = [old_to_new[b] for b in self.basis]
        self.artificials = []

    def _run_phase(
        self,
        cj: List[float],
        allowed_cols: List[int],
        sense: str,
        phase: int,
    ) -> bool:
        iter_num = 0
        while True:
            zj_cj, z = self._compute_zj_cj(cj)
            col, col_reason = self._choose_pivot_column(zj_cj, allowed_cols, sense)

            if col is None:
                self._snapshot(
                    phase=phase,
                    iter_num=iter_num,
                    cj=cj,
                    zj_cj=zj_cj,
                    z=z,
                    pivot=None,
                    ops=[],
                    description=(
                        f"Fase {phase} terminada en la iteración {iter_num}. "
                        f"{col_reason}."
                    ),
                )
                return True

            row, row_reason = self._choose_pivot_row(col)
            if row is None:
                self._snapshot(
                    phase=phase,
                    iter_num=iter_num,
                    cj=cj,
                    zj_cj=zj_cj,
                    z=z,
                    pivot=None,
                    ops=[],
                    description=f"Fase {phase}: {row_reason}.",
                )
                return False

            entering = self.var_names[col]
            leaving = self.var_names[self.basis[row]]
            pivot_val = self.A[row][col]
            pivot_info = PivotInfo(
                column_index=col,
                column_variable=entering,
                column_reason=col_reason,
                row_index=row,
                row_label=self.row_labels[row],
                row_reason=row_reason,
                pivot_value=float(pivot_val),
            )
            description = (
                f"Fase {phase} · Iteración {iter_num + 1}. "
                f"Entra {entering} y sale {leaving}. "
                f"Pivote = {self._fmt(pivot_val)} en {self.row_labels[row]}, "
                f"columna {entering}. {col_reason}. {row_reason}."
            )

            snapshot_index = self._snapshot(
                phase=phase,
                iter_num=iter_num,
                cj=cj,
                zj_cj=zj_cj,
                z=z,
                pivot=pivot_info,
                ops=[],
                description=description,
            )

            ops = self._pivot(row, col)
            self.iterations[snapshot_index].row_operations = ops

            iter_num += 1
            if iter_num > MAX_ITERATIONS:
                self._snapshot(
                    phase=phase,
                    iter_num=iter_num,
                    cj=cj,
                    zj_cj=zj_cj,
                    z=z,
                    pivot=None,
                    ops=[],
                    description=(
                        f"Fase {phase}: se excedió el límite de {MAX_ITERATIONS} "
                        "iteraciones."
                    ),
                )
                return False

    # ------------------------------------------------------------------
    # Snapshot de una iteración
    # ------------------------------------------------------------------
    def _snapshot(
        self,
        phase: int,
        iter_num: int,
        cj: List[float],
        zj_cj: List[float],
        z: float,
        pivot: Optional[PivotInfo],
        ops: List[RowOperation],
        description: str,
    ) -> int:
        rows: List[TableRow] = []
        for i, row_coefs in enumerate(self.A):
            basic_idx = self.basis[i]
            rows.append(
                TableRow(
                    label=self.row_labels[i],
                    cb=float(cj[basic_idx]),
                    basic_var=self.var_names[basic_idx],
                    coefficients=[float(x) for x in row_coefs],
                    bi=float(self.b[i]),
                )
            )

        iteration = Iteration(
            phase=phase,
            iteration=iter_num,
            description=description,
            cj=[float(x) for x in cj],
            variables=list(self.var_names),
            rows=rows,
            zj_cj=[float(x) for x in zj_cj],
            z=float(z),
            pivot=pivot,
            row_operations=ops,
        )
        self.iterations.append(iteration)
        return len(self.iterations) - 1

    # ------------------------------------------------------------------
    # Resultado final
    # ------------------------------------------------------------------
    def _final_result(self) -> dict:
        cj_original = [0.0] * len(self.var_names)
        for i in range(self.n_vars):
            cj_original[i] = self.original_c[i]
        _, z = self._compute_zj_cj(cj_original)

        solution = {self.var_names[i]: 0.0 for i in range(self.n_vars)}
        for row_idx, basic in enumerate(self.basis):
            if basic < self.n_vars:
                solution[self.var_names[basic]] = float(self.b[row_idx])

        return TwoPhaseResult(
            status="optimal",
            z=float(z),
            basis=[self.var_names[i] for i in self.basis],
            solution=solution,
            phase_one_setup=self.phase_one_setup,
            phase_two_setup=self.phase_two_setup,
            iterations=self.iterations,
        ).model_dump()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _fmt(x: float) -> str:
        if x is None:
            return "0"
        if abs(x - round(x)) < 1e-9:
            return str(int(round(x)))
        return f"{x:.4f}".rstrip("0").rstrip(".")


def solve_two_steps(payload) -> dict:
    return TwoPhaseSolver(payload).solve()
