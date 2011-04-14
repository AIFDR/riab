from django.contrib import admin
from impact.models import Calculation, Server, Workspace


class CalculationAdmin(admin.ModelAdmin):
    date_hierarchy = 'run_date'
    list_filter = 'user', 'impact_function', 'success'
    list_display = ('run_date', 'success', 'user', 'errors',
                    'run_duration', 'layer', 'exposure_layer',
                    'hazard_layer', 'impact_function')

admin.site.register(Calculation, CalculationAdmin)
admin.site.register([Server, Workspace])
