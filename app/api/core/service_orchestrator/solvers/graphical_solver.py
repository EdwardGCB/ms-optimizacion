"""
Solver del método gráfico para programación lineal con 2 variables.

Este módulo resuelve problemas de la forma:

    MAX/MIN z = c1*X1 + c2*X2
    sujeto a:
        a1*X1 + a2*X2 <= b   (o >=, =)
        X1 >= 0, X2 >= 0

Metodología
-----------
1. **Trazado de restricciones**
   Cada restricción se convierte en su recta frontera igualando la
   expresión al valor límite: ``a1*X1 + a2*X2 = b``.
   Luego se despejan los puntos donde la recta corta los ejes:
   - Con X2 = 0  →  X1 = b / a1
   - Con X1 = 0  →  X2 = b / a2

2. **Intersecciones**
   Se calculan todos los puntos donde se cruzan las rectas de las
   restricciones y los ejes coordenados (X1=0, X2=0).

3. **Región factible**
   De esos puntos se conservan solo los que cumplen todas las
   restricciones y la no negatividad (X1 >= 0, X2 >= 0).

4. **Solución óptima**
   Se evalúa z = c1*X1 + c2*X2 en cada vértice factible y se elige:
   - El de **mayor** z si el problema es MAX.
   - El de **menor** z si el problema es MIN.

5. **Recta objetivo**
   Se genera una recta paralela a la función objetivo que pasa por
   el punto óptimo, para que el frontend pueda graficarla.

Estructura de respuesta
-----------------------
La respuesta incluye todos los datos necesarios para renderizar
la solución en el frontend:

- ``restrictions[]``       → rectas con interceptos y plot_points
- ``intersection_points[]``→ todos los puntos de cruce calculados
- ``feasible_vertices[]``  → vértices de la región factible
- ``optimal_point``        → vértice óptimo con explicación textual
- ``objective_line``       → puntos para trazar la recta objetivo
"""

from typing import List, Optional, Tuple

# Tolerancia numérica para comparaciones de punto flotante.
EPS = 1e-9


class GraphicalSolver:
    """
    Resuelve problemas de programación lineal con exactamente 2 variables
    mediante el método gráfico.

    Attributes:
        sense (str): Tipo de optimización, ``"MAX"`` o ``"MIN"``.
        c (List[float]): Coeficientes [c1, c2] de la función objetivo.
        restrictions: Lista de restricciones del payload de entrada.

    Raises:
        ValueError: Si el problema tiene más o menos de 2 variables.
    """

    def __init__(self, payload):
        """
        Inicializa el solver con los datos del request.

        Args:
            payload: Instancia de ``CreateOptimizationRequest`` con
                nro_variables=2, coeficientes objetivo y restricciones.
        """
        if payload.nro_variables != 2:
            raise ValueError("El método gráfico solo soporta 2 variables")

        self.sense: str = payload.optimization.value
        self.c: List[float] = [float(x) for x in payload.coefficients]
        self.restrictions = payload.restrictions

    def solve(self) -> dict:
        """
        Ejecuta el método gráfico completo y devuelve el resultado.

        Flujo:
            1. Normaliza restricciones (ajusta signos si b < 0).
            2. Construye las rectas con interceptos en los ejes.
            3. Calcula intersecciones entre todas las rectas.
            4. Filtra vértices factibles.
            5. Selecciona el óptimo o detecta infactibilidad/no acotación.

        Returns:
            dict con ``status`` (``optimal`` | ``infeasible`` | ``unbounded``),
            puntos para graficar, vértices factibles y punto óptimo.
        """
        normalized = self._normalize_restrictions()
        restriction_lines = self._build_restriction_lines(normalized)
        intersection_points = self._find_intersection_points(normalized)
        feasible_vertices = [p for p in intersection_points if p["feasible"]]

        if not feasible_vertices:
            return {
                "status": "infeasible",
                "method": "graphical",
                "z": None,
                "solution": {"X1": 0.0, "X2": 0.0},
                "objective": self._objective_payload(),
                "restrictions": restriction_lines,
                "intersection_points": intersection_points,
                "feasible_vertices": [],
                "optimal_point": None,
            }

        optimal = self._select_optimal(feasible_vertices)
        if self._is_unbounded(optimal, normalized):
            return {
                "status": "unbounded",
                "method": "graphical",
                "z": None,
                "solution": {"X1": 0.0, "X2": 0.0},
                "objective": self._objective_payload(),
                "restrictions": restriction_lines,
                "intersection_points": intersection_points,
                "feasible_vertices": feasible_vertices,
                "optimal_point": None,
            }

        return {
            "status": "optimal",
            "method": "graphical",
            "z": optimal["z"],
            "solution": {"X1": optimal["x"], "X2": optimal["y"]},
            "objective": self._objective_payload(),
            "restrictions": restriction_lines,
            "intersection_points": intersection_points,
            "feasible_vertices": feasible_vertices,
            "optimal_point": optimal,
            "objective_line": self._objective_line_through(optimal),
        }

    # ------------------------------------------------------------------
    # Normalización
    # ------------------------------------------------------------------
    def _normalize_restrictions(self) -> List[dict]:
        """
        Normaliza cada restricción para facilitar el cálculo gráfico.

        Si el lado derecho ``b`` es negativo, multiplica toda la ecuación
        por -1 e invierte el operador (``<=`` ↔ ``>=``).

        Returns:
            Lista de dicts con claves ``a1``, ``a2``, ``b``, ``operator``,
            ``text`` (restricción original) y ``line_text`` (recta frontera).
        """
        normalized = []
        for idx, r in enumerate(self.restrictions):
            a1 = float(r.coefficients[0])
            a2 = float(r.coefficients[1])
            b = float(r.value)
            op = r.operator.value

            if b < 0:
                a1, a2, b = -a1, -a2, -b
                if op == "<=":
                    op = ">="
                elif op == ">=":
                    op = "<="

            normalized.append(
                {
                    "index": idx,
                    "a1": a1,
                    "a2": a2,
                    "b": b,
                    "operator": op,
                    "text": self._restriction_text(a1, a2, op, b),
                    "line_text": self._line_text(a1, a2, b),
                }
            )
        return normalized

    # ------------------------------------------------------------------
    # Rectas por restricción
    # ------------------------------------------------------------------
    def _build_restriction_lines(self, normalized: List[dict]) -> List[dict]:
        """
        Construye la información de cada recta para el frontend.

        Para cada restricción calcula:
        - ``intercept_x``: punto donde la recta corta el eje X (X2=0).
        - ``intercept_y``: punto donde la recta corta el eje Y (X1=0).
        - ``plot_points``: par de puntos mínimo para trazar la recta.

        Args:
            normalized: Restricciones ya normalizadas.

        Returns:
            Lista de rectas lista para renderizar en el plano cartesiano.
        """
        lines = []
        for r in normalized:
            a1, a2, b = r["a1"], r["a2"], r["b"]
            intercept_x = self._intercept_on_axis(a1, a2, b, axis="x")
            intercept_y = self._intercept_on_axis(a1, a2, b, axis="y")
            plot_points = self._line_plot_points(a1, a2, b, intercept_x, intercept_y)

            lines.append(
                {
                    "index": r["index"],
                    "coefficients": [a1, a2],
                    "operator": r["operator"],
                    "value": b,
                    "text": r["text"],
                    "line_text": r["line_text"],
                    "intercept_x": intercept_x,
                    "intercept_y": intercept_y,
                    "plot_points": plot_points,
                }
            )
        return lines

    def _intercept_on_axis(
        self,
        a1: float,
        a2: float,
        b: float,
        axis: str,
    ) -> Optional[dict]:
        """
        Despeja el intercepto de la recta ``a1*X1 + a2*X2 = b`` con un eje.

        Args:
            a1, a2, b: Coeficientes de la recta frontera.
            axis: ``"x"`` para cortar el eje X (X2=0), ``"y"`` para el eje Y.

        Returns:
            Dict con coordenadas (x, y), etiqueta y cálculo paso a paso,
            o ``None`` si la recta es paralela a ese eje.
        """
        if axis == "x":
            if abs(a1) < EPS:
                return None
            x = b / a1
            return {
                "x": float(x),
                "y": 0.0,
                "label": f"X2=0 → X1={self._fmt(x)}",
                "calculation": f"{self._fmt(b)}/{self._fmt(a1)} = {self._fmt(x)}",
            }

        if abs(a2) < EPS:
            return None
        y = b / a2
        return {
            "x": 0.0,
            "y": float(y),
            "label": f"X1=0 → X2={self._fmt(y)}",
            "calculation": f"{self._fmt(b)}/{self._fmt(a2)} = {self._fmt(y)}",
        }

    def _line_plot_points(
        self,
        a1: float,
        a2: float,
        b: float,
        intercept_x: Optional[dict],
        intercept_y: Optional[dict],
    ) -> List[dict]:
        """
        Genera al menos dos puntos para trazar una restricción en el gráfico.

        Casos especiales:
        - Recta oblicua: usa los dos interceptos en los ejes.
        - Recta vertical (a2=0): dos puntos con la misma X.
        - Recta horizontal (a1=0): dos puntos con la misma Y.
        - Un solo intercepto: extiende la recta con la pendiente calculada.
        """
        points: List[dict] = []
        if intercept_x:
            points.append({"x": intercept_x["x"], "y": intercept_x["y"]})
        if intercept_y:
            points.append({"x": intercept_y["x"], "y": intercept_y["y"]})

        if len(points) >= 2:
            return points

        if abs(a2) < EPS and abs(a1) >= EPS:
            x_val = b / a1
            return [
                {"x": float(x_val), "y": 0.0},
                {"x": float(x_val), "y": 10.0},
            ]

        if abs(a1) < EPS and abs(a2) >= EPS:
            y_val = b / a2
            return [
                {"x": 0.0, "y": float(y_val)},
                {"x": 10.0, "y": float(y_val)},
            ]

        if len(points) == 1:
            p = points[0]
            if abs(a1) >= EPS:
                slope = -a1 / a2 if abs(a2) >= EPS else 0.0
                return [
                    p,
                    {"x": p["x"] + 5.0, "y": p["y"] + slope * 5.0},
                ]

        return points

    # ------------------------------------------------------------------
    # Intersecciones
    # ------------------------------------------------------------------
    def _find_intersection_points(self, normalized: List[dict]) -> List[dict]:
        """
        Calcula todos los puntos de intersección entre rectas del problema.

        Considera las rectas de cada restricción (R1, R2, ...) más los
        ejes X1=0 y X2=0. Para cada par de rectas no paralelas resuelve
        el sistema 2x2 y evalúa si el punto es factible.

        Returns:
            Lista de puntos con coordenadas, valor de z, factibilidad,
            rectas de origen y descripción textual para mostrar al usuario.
        """
        line_defs = [
            {"label": f"R{r['index'] + 1}", "a1": r["a1"], "a2": r["a2"], "b": r["b"]}
            for r in normalized
        ]
        line_defs.extend(
            [
                {"label": "X1=0", "a1": 1.0, "a2": 0.0, "b": 0.0},
                {"label": "X2=0", "a1": 0.0, "a2": 1.0, "b": 0.0},
            ]
        )

        raw_points: List[Tuple[float, float, List[str]]] = []
        for i in range(len(line_defs)):
            for j in range(i + 1, len(line_defs)):
                point = self._intersect_lines(line_defs[i], line_defs[j])
                if point is None:
                    continue
                x, y = point
                sources = [line_defs[i]["label"], line_defs[j]["label"]]
                raw_points.append((x, y, sources))

        unique: List[dict] = []
        for x, y, sources in raw_points:
            if any(abs(x - p["x"]) < EPS and abs(y - p["y"]) < EPS for p in unique):
                continue

            z = self._evaluate_z(x, y)
            feasible = self._is_feasible(x, y, normalized)
            unique.append(
                {
                    "label": f"P{len(unique) + 1}",
                    "x": float(x),
                    "y": float(y),
                    "z": float(z),
                    "feasible": feasible,
                    "from_lines": sources,
                    "description": (
                        f"Intersección de {' y '.join(sources)}: "
                        f"({self._fmt(x)}, {self._fmt(y)})"
                    ),
                }
            )

        return unique

    def _intersect_lines(self, l1: dict, l2: dict) -> Optional[Tuple[float, float]]:
        """
        Resuelve la intersección de dos rectas usando regla de Cramer.

        Sistema:
            a1*X1 + a2*X2 = b1
            c1*X1 + c2*X2 = b2

        Returns:
            Tupla (X1, X2) o ``None`` si las rectas son paralelas (det=0).
        """
        det = l1["a1"] * l2["a2"] - l1["a2"] * l2["a1"]
        if abs(det) < EPS:
            return None

        x = (l1["b"] * l2["a2"] - l1["a2"] * l2["b"]) / det
        y = (l1["a1"] * l2["b"] - l1["b"] * l2["a1"]) / det
        return x, y

    # ------------------------------------------------------------------
    # Factibilidad y óptimo
    # ------------------------------------------------------------------
    def _is_feasible(self, x: float, y: float, normalized: List[dict]) -> bool:
        """
        Verifica si el punto (x, y) pertenece a la región factible.

        Comprueba:
        - No negatividad: X1 >= 0 y X2 >= 0.
        - Cada restricción según su operador (<=, >=, =).
        """
        if x < -EPS or y < -EPS:
            return False

        for r in normalized:
            lhs = r["a1"] * x + r["a2"] * y
            op = r["operator"]
            b = r["b"]

            if op == "<=" and lhs > b + EPS:
                return False
            if op == ">=" and lhs < b - EPS:
                return False
            if op == "=" and abs(lhs - b) > EPS:
                return False

        return True

    def _evaluate_z(self, x: float, y: float) -> float:
        """Evalúa la función objetivo z = c1*X1 + c2*X2 en un punto."""
        return self.c[0] * x + self.c[1] * y

    def _select_optimal(self, feasible_vertices: List[dict]) -> dict:
        """
        Selecciona el vértice óptimo entre los puntos factibles.

        Para MAX elige el vértice con mayor z; para MIN el de menor z.
        Incluye una explicación textual del criterio de selección.
        """
        if self.sense == "MAX":
            best = max(feasible_vertices, key=lambda p: p["z"])
            reason = (
                f"Mayor valor de z entre los vértices factibles: "
                f"z = {self._fmt(best['z'])} en ({self._fmt(best['x'])}, "
                f"{self._fmt(best['y'])})"
            )
        else:
            best = min(feasible_vertices, key=lambda p: p["z"])
            reason = (
                f"Menor valor de z entre los vértices factibles: "
                f"z = {self._fmt(best['z'])} en ({self._fmt(best['x'])}, "
                f"{self._fmt(best['y'])})"
            )

        return {
            "label": "P*",
            "x": best["x"],
            "y": best["y"],
            "z": best["z"],
            "from_lines": best["from_lines"],
            "reason": reason,
        }

    def _is_unbounded(self, optimal: dict, normalized: List[dict]) -> bool:
        """
        Detecta si el problema es no acotado desde el vértice óptimo candidato.

        Analiza direcciones a lo largo de las restricciones activas en el
        vértice. Si existe una dirección que mejora z y permanece factible
        para valores grandes de t, el problema no tiene solución finita.
        """
        c1, c2 = self.c
        x, y = optimal["x"], optimal["y"]

        candidate_dirs: List[Tuple[float, float]] = []
        for r in normalized:
            lhs = r["a1"] * x + r["a2"] * y
            if abs(lhs - r["b"]) > EPS and r["operator"] != "=":
                continue
            if r["operator"] == "=" and abs(lhs - r["b"]) > EPS:
                continue
            a1, a2 = r["a1"], r["a2"]
            candidate_dirs.extend([(-a2, a1), (a2, -a1)])

        if abs(x) < EPS:
            candidate_dirs.append((1.0, 0.0))
        if abs(y) < EPS:
            candidate_dirs.append((0.0, 1.0))

        for dx, dy in candidate_dirs:
            if abs(dx) < EPS and abs(dy) < EPS:
                continue
            grad = c1 * dx + c2 * dy
            improves = (self.sense == "MAX" and grad > EPS) or (
                self.sense == "MIN" and grad < -EPS
            )
            if not improves:
                continue
            if not self._direction_feasible_at_point(x, y, dx, dy, normalized):
                continue
            if self._ray_is_feasible(x, y, dx, dy, normalized):
                return True

        return False

    def _direction_feasible_at_point(
        self,
        x: float,
        y: float,
        dx: float,
        dy: float,
        normalized: List[dict],
    ) -> bool:
        """
        Verifica si la dirección (dx, dy) es factible en el punto (x, y).

        Usa condiciones de primer orden: no puede salir de la región factible
        al moverse infinitesimalmente en esa dirección.
        """
        if x <= EPS and dx < -EPS:
            return False
        if y <= EPS and dy < -EPS:
            return False

        for r in normalized:
            a1, a2, b = r["a1"], r["a2"], r["b"]
            lhs = a1 * x + a2 * y
            d_lhs = a1 * dx + a2 * dy

            if r["operator"] == "<=":
                if lhs > b + EPS:
                    return False
                if abs(lhs - b) < EPS and d_lhs > EPS:
                    return False
            elif r["operator"] == ">=":
                if lhs < b - EPS:
                    return False
                if abs(lhs - b) < EPS and d_lhs < -EPS:
                    return False
            elif r["operator"] == "=":
                if abs(lhs - b) > EPS:
                    return False
                if abs(d_lhs) > EPS:
                    return False

        return True

    def _ray_is_feasible(
        self,
        x: float,
        y: float,
        dx: float,
        dy: float,
        normalized: List[dict],
    ) -> bool:
        """
        Comprueba si el rayo (x, y) + t*(dx, dy) permanece factible
        para t creciente (t = 1, 10, 100, 1000).
        """
        for t in (1.0, 10.0, 100.0, 1000.0):
            if not self._is_feasible(x + t * dx, y + t * dy, normalized):
                return False
        return True

    def _objective_line_through(self, optimal: dict) -> dict:
        """
        Genera puntos para trazar la recta objetivo en el gráfico.

        La recta es paralela a z = c1*X1 + c2*X2 y pasa por el punto
        óptimo, permitiendo visualizar la función objetivo en su valor
        óptimo.
        """
        c1, c2 = self.c
        x0, y0 = optimal["x"], optimal["y"]

        if abs(c2) >= EPS:
            sample = [
                {"x": x0 - 2.0, "y": y0 + (c1 / c2) * 2.0},
                {"x": x0, "y": y0},
                {"x": x0 + 2.0, "y": y0 - (c1 / c2) * 2.0},
            ]
        else:
            sample = [
                {"x": x0, "y": y0 - 2.0},
                {"x": x0, "y": y0},
                {"x": x0, "y": y0 + 2.0},
            ]

        return {
            "through_point": {"x": x0, "y": y0},
            "direction": {"dx": c1, "dy": c2},
            "plot_points": sample,
            "text": self._objective_payload()["text"],
        }

    def _objective_payload(self) -> dict:
        """Devuelve la función objetivo en formato estructurado para el front."""
        return {
            "sense": self.sense,
            "coefficients": self.c,
            "text": self._format_objective(),
        }

    # ------------------------------------------------------------------
    # Helpers de texto
    # ------------------------------------------------------------------
    def _restriction_text(self, a1: float, a2: float, op: str, b: float) -> str:
        """Formatea la restricción con su operador original (<=, >=, =)."""
        left = self._format_expression(a1, a2)
        return f"{left} {op} {self._fmt(b)}"

    def _line_text(self, a1: float, a2: float, b: float) -> str:
        """Formatea la recta frontera como ecuación igualada (a1*X1 + a2*X2 = b)."""
        left = self._format_expression(a1, a2)
        return f"{left} = {self._fmt(b)}"

    def _format_objective(self) -> str:
        """Formatea la función objetivo como texto legible (MAX/MIN z = ...)."""
        left = self._format_expression(self.c[0], self.c[1], "X1", "X2")
        return f"{self.sense} z = {left}"

    def _format_expression(
        self,
        a1: float,
        a2: float,
        v1: str = "X1",
        v2: str = "X2",
    ) -> str:
        """Construye una expresión algebraica legible a partir de coeficientes."""
        parts: List[str] = []
        for coef, name in ((a1, v1), (a2, v2)):
            if abs(coef) < EPS:
                continue
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
        return " ".join(parts) if parts else "0"

    @staticmethod
    def _fmt(x: float) -> str:
        """Formatea un número eliminando decimales innecesarios."""
        if abs(x - round(x)) < EPS:
            return str(int(round(x)))
        return f"{x:.4f}".rstrip("0").rstrip(".")


def solve_graphical(payload) -> dict:
    """
    Punto de entrada del solver gráfico.

    Args:
        payload: Request con type_optimization=``graphical`` y 2 variables.

    Returns:
        Resultado completo del método gráfico listo para persistir
        en MongoDB y renderizar en el frontend.
    """
    return GraphicalSolver(payload).solve()
