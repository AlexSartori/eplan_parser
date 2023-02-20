import eplan_parser.output_parser


def export_to_json(fname: str, dataset: dict) -> None:
    return eplan_parser.output_parser.export_to_jspon(fname, dataset)

def load_dataset(fname: str) -> dict:
    return eplan_parser.output_parser.load_dataset(fname)

