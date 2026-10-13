"""Bundle-local Python runner for original Nature CSV templates; no AI image calls."""
import importlib.util
import json
from pathlib import Path
import sys


def main():
    root = Path(__file__).resolve().parent
    sys.path.insert(0,str(root/'tools'))
    spec = importlib.util.spec_from_file_location('local_nature_templates',root/'tools/plot_templates.py')
    templates = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(templates)
    templates.require_dependencies()
    # NumPy <2 names the same trapezoidal integration operation trapz.
    if not hasattr(templates.np, 'trapezoid'):
        templates.np.trapezoid = templates.np.trapz
    configure = templates.configure_style
    save = templates.save_bundle

    def slide_style():
        configure()
        templates.mpl.rcParams.update({'font.sans-serif':['Microsoft YaHei','Arial','DejaVu Sans'],
            'font.size':18,'axes.labelsize':18,'axes.titlesize':20,'xtick.labelsize':16,
            'ytick.labelsize':16,'legend.fontsize':16,'svg.fonttype':'none','pdf.fonttype':42})

    def audited_save(fig, output):
        # The adapted source performs alignment before exporting any figure.
        paths = save(fig,output)
        fig.savefig(root/'figure.png',dpi=300,bbox_inches='tight',facecolor='white')
        return paths

    templates.configure_style = slide_style
    templates.save_bundle = audited_save
    arguments = json.loads((root/'plot-arguments.json').read_text(encoding='utf-8'))
    return templates.main(arguments)


if __name__ == '__main__':
    raise SystemExit(main())
