import sys
import os
sys.path.append('/home/enyelber/Escritorio/ODOO18_New/odoo-server')
import odoo
odoo.tools.config.parse_config(['-c', '/home/enyelber/Escritorio/ODOO18_New/odoo-server/soft.conf', '-d', 'mi_empresa'])
reg = odoo.registry('mi_empresa')
with reg.cursor() as cr:
    env = odoo.api.Environment(cr, 1, {})
    record = env['gym.horario.report.wizard'].search([], limit=1)
    if not record:
        print("No wizard found")
        sys.exit()
    action = env['ir.actions.report'].search([('report_name', '=', 'horarios_clan_jiu_jitsu.report_horario_semanal_template')], limit=1)
    try:
        html, ext = action._render_qweb_html(record.ids, data={'area': '1'})
        print(html.decode('utf-8'))
    except Exception as e:
        import traceback
        traceback.print_exc()
