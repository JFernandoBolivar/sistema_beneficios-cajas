-- =============================================
-- Script SQL para crear índices de optimización
-- Ejecutar una sola vez en la base de datos
-- =============================================

-- Índices para la tabla personal
CREATE INDEX IF NOT EXISTS idx_personal_cedula ON personal(Cedula);
CREATE INDEX IF NOT EXISTS idx_personal_estatus ON personal(Estatus);
CREATE INDEX IF NOT EXISTS idx_personal_tipo_nomina ON personal(typeNomina);
CREATE INDEX IF NOT EXISTS idx_personal_estatus_nomina ON personal(Estatus, typeNomina);

-- Índices para la tabla delivery
CREATE INDEX IF NOT EXISTS idx_delivery_data_id ON delivery(Data_ID);
CREATE INDEX IF NOT EXISTS idx_delivery_staff_id ON delivery(Staff_ID);
CREATE INDEX IF NOT EXISTS idx_delivery_time_box ON delivery(Time_box);

-- Índices para la tabla autorizados
CREATE INDEX IF NOT EXISTS idx_autorizados_beneficiado ON autorizados(beneficiado);
CREATE INDEX IF NOT EXISTS idx_autorizados_cedula ON autorizados(Cedula);

-- Índices para la tabla user_history
CREATE INDEX IF NOT EXISTS idx_history_cedula ON user_history(cedula);
CREATE INDEX IF NOT EXISTS idx_history_cedula_personal ON user_history(cedula_personal);
CREATE INDEX IF NOT EXISTS idx_history_time_login ON user_history(time_login);
CREATE INDEX IF NOT EXISTS idx_history_action ON user_history(action);

-- Índices para la tabla apoyo
CREATE INDEX IF NOT EXISTS idx_apoyo_fecha ON apoyo(Fecha);
CREATE INDEX IF NOT EXISTS idx_apoyo_ci_autorizado ON apoyo(CI_autorizado);

-- =============================================
-- Verificar índices creados
-- =============================================
SHOW INDEX FROM personal;
SHOW INDEX FROM delivery;
SHOW INDEX FROM autorizados;
SHOW INDEX FROM user_history;
SHOW INDEX FROM apoyo;
