import getpass
import flask
import allforks

DEBUG = getpass.getuser() in ['andrei']
app = flask.Flask(__name__)


@app.route('/<owner>/<repo>')
def index(owner, repo):
    # full_name = flask.request.args.get('repo')
    data = allforks.get_forks(full_name='%s/%s' % (owner, repo))
    lines = allforks.format_forks(data)
    return flask.Response('\n'.join(lines), mimetype='text/plain')


if __name__ == '__main__':
    app.run(debug=DEBUG)
