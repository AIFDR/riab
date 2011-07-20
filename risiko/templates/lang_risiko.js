{% extends "lang.js" %}

{% block extra_lang %}
if (window.GeoExplorer) {
      Ext.apply(GeoExplorer.prototype, {
        hazardComboLabelText: gettext("Hazard"),
        exposureComboLabelText: gettext("Exposure"),
        functionComboLabelText: gettext("Function"),
        resetButtonText: gettext("Reset"),
        calculateButtonText: gettext("Calculate"),
        calculatingText: gettext("Calculating"),
        calculatorTitleText: gettext("Impact Calculator"),
        hazardSelectText: gettext("Select Hazard ..."),
        exposureSelectText: gettext("Select Exposure ..."),
        functionSelectText: gettext("Select Function ...")
  });
}
{% endblock %}
