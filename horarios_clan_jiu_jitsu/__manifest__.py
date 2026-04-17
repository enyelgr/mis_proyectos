{
    'name': 'Horarios Clan Jiu Jitsu',
    'summary': 'Gestión de horarios, instructores y áreas para el club Jiu Jitsu',
    'description': 'Módulo para gestionar bloques de horario, instructores y áreas.',
    'author': 'Enyelber',
    'website': '',
    'category': 'Sports/Facilities',
    'version': '1.1',
    'icon': '/horarios_clan_jiu_jitsu/static/description/icon.png',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/wizards_views.xml',
        'reports/report_horario_area.xml',
        'views/vistas.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'assets': {
        'web.assets_backend': [
            'horarios_clan_jiu_jitsu/static/src/css/schedule_board.css',
            'horarios_clan_jiu_jitsu/static/src/js/calendar_controller.js',
        ]
    },
}
