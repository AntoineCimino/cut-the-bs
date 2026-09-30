import main


def test_entry_point_parser_accepts_url():
    assert main.build_parser().parse_args(["https://youtu.be/synthetic01"]).url == "https://youtu.be/synthetic01"
