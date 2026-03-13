from flask import render_template, redirect, url_for, request, current_app
from flask_login import login_required, current_user
from app.main import bp
from app import dataset_manager
from app.utils import sanitise_form_inputs
from urllib.parse import urlsplit

@bp.before_request
def check_for_dataset():
    if not dataset_manager.dataset_exists() and not request.endpoint in ["main.onboarding", "main.index"]:
        return redirect(url_for("main.onboarding", step="1", next=request.url))

@bp.route("/")
@bp.route("/index")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("index.html")

@bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("views/dashboard.html")

@bp.route("/onboarding", methods=["GET", "POST"])
@login_required
def onboarding():
    def download_callback(blocknum: int, blocksize: int, totalsize: int):
        readed_data = blocknum * blocksize
        if totalsize > 0:
            download_percentage = readed_data * 100 / totalsize
            if ( download_percentage <= 100 ):
                print(f"Download progress: {download_percentage}%")
    if request.method == "POST":
        values = sanitise_form_inputs(request=request, fields=["dataset"])
        dataset = values["dataset"]

        if dataset:
            dataset_manager.download_dataset(current_app.config["DATASET_URLS"][dataset], progress_callback=download_callback)
            next_page = request.args.get("next")
            if not next_page or urlsplit(next_page).netloc != "":
                next_page = url_for("main.dashboard")
            return redirect(next_page)

    return render_template("onboarding.html")