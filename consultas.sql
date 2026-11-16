-- Consultas sobre la tabla salidas (data/salidas_2025_limpio.csv), compatibles con SQLite / MySQL 8+

-- 1. Salidas por mes y variación respecto del mes anterior
WITH m AS (SELECT mes, COUNT(*) AS salidas FROM salidas GROUP BY mes)
SELECT mes, salidas,
       salidas - LAG(salidas) OVER (ORDER BY mes) AS variacion
FROM m ORDER BY mes;

-- 2. Participación de cada departamento en el total de salidas
SELECT departamento, COUNT(*) AS salidas,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS porcentaje
FROM salidas
WHERE departamento IS NOT NULL
GROUP BY departamento
ORDER BY salidas DESC;

-- 3. Qué sistema genera más trabajo y de qué tipo (inspección vs. recambio/reparación)
SELECT sistema,
       COUNT(*) AS total,
       SUM(CASE WHEN tipo_trabajo = 'Inspección / diagnóstico' THEN 1 ELSE 0 END) AS inspecciones,
       SUM(CASE WHEN tipo_trabajo = 'Recambio / instalación'  THEN 1 ELSE 0 END) AS recambios,
       SUM(CASE WHEN tipo_trabajo = 'Reparación'              THEN 1 ELSE 0 END) AS reparaciones
FROM salidas
GROUP BY sistema
ORDER BY total DESC;

-- 4. Pozos reincidentes: 3 o más salidas en el año
WITH visitas AS (
    SELECT id_pozo, COUNT(*) AS n_salidas,
           MIN(fecha) AS primera, MAX(fecha) AS ultima
    FROM salidas
    WHERE id_pozo IS NOT NULL
    GROUP BY id_pozo
)
SELECT * FROM visitas WHERE n_salidas >= 3 ORDER BY n_salidas DESC, id_pozo;

-- 5. Días promedio entre salidas consecutivas al mismo pozo
WITH ordenadas AS (
    SELECT id_pozo, fecha,
           JULIANDAY(fecha) - JULIANDAY(LAG(fecha) OVER (PARTITION BY id_pozo ORDER BY fecha)) AS dias_desde_anterior
    FROM salidas
    WHERE id_pozo IS NOT NULL
)
SELECT COUNT(dias_desde_anterior) AS revisitas,
       ROUND(AVG(dias_desde_anterior), 1) AS dias_promedio,
       SUM(CASE WHEN dias_desde_anterior <= 30 THEN 1 ELSE 0 END) AS revisitas_en_30_dias
FROM ordenadas;

-- 6. Peso de las fallas eléctricas y de tablero por departamento
SELECT departamento,
       COUNT(*) AS salidas,
       SUM(CASE WHEN sistema IN ('Tablero y protecciones','Falla eléctrica / cableado') THEN 1 ELSE 0 END) AS electricas,
       ROUND(100.0 * SUM(CASE WHEN sistema IN ('Tablero y protecciones','Falla eléctrica / cableado') THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_electricas
FROM salidas
WHERE departamento IS NOT NULL
GROUP BY departamento
HAVING COUNT(*) >= 20
ORDER BY pct_electricas DESC;
