import pytest

@pytest.mark.parametrize("cmd,expected_in_stdout,expected_in_stderr", [
    (["script", "run", "hello.py"], ["hello world"], []),
    (["script", "list"], ["hello.py"], []),
    (["script", "show", "hello.py"], ["print('hello world')"], []),
    (["profile", "list"], ["slurm"], []),
    (["profile", "show", "slurm"], ["cluster"], []),
    (["env", "list"], ["wget"], []),
    (["env", "show", "wget"], ["wget"], []),
    (["env", "create"], ["All conda environments created!"], []),
    (["env", "create", "wget"], ["Created environment wget!"], []),
    (["env", "run", "wget", "which wget"], [".conda"], []),
    (["env", "activate", "wget"], [], ["Activating wget environment...", "Exiting wget environment..."]),
    (["env", "remove", "-f"], ["Deleted"], []),
    (["info"], ["name", "version", "snakefile", "conda_prefix_dir", "singularity_prefix_dir", "workflow_dir_path"], []),
])
def test_snk_cli_command(capfd, local_runner, cmd, expected_in_stdout, expected_in_stderr):
    res = local_runner(cmd)
    captured = capfd.readouterr()  # Capture stdout and stderr of subprocess e.g. env and script commands
    assert res.exit_code == 0, res.stderr
    for expected in expected_in_stdout:
        assert expected in res.stdout or expected in captured.out, res.stderr
    for expected in expected_in_stderr:
        assert expected in res.stderr or expected in captured.err, res.stderr