from core.handler import Handler
from core.utils import *


def make_code_block(language, string):
    return "```{language}\n{string}\n```".format(language=language, string=string)


class Hover(Handler):
    name = "hover"
    method = "textDocument/hover"

    def process_request(self, position) -> dict:
        return dict(position=position)

    def parse_hover_contents(self, contents, render_strings):
        content_type = type(contents)
        if content_type == str:
            if contents.startswith("```"):
                render_strings.append(contents)
            else:
                render_strings.append(make_code_block("text", contents))
        elif content_type == dict:
            if "kind" in contents:
                # Some language servers will return plaintext as the kind with the markdown format as value, such as erlang_ls
                if contents["kind"] == "markdown" or contents["kind"] == "plaintext":
                    render_strings.append(contents["value"])
                else:
                    lsp_server = self.file_action.get_match_lsp_servers("hover")[0]
                    render_strings.append(make_code_block(
                        lsp_server.get_language_id(self.file_action),
                        contents["value"]
                    ))
            elif "language" in contents:
                render_strings.append(make_code_block(contents["language"], contents["value"]))
        elif content_type == list:
            for item in contents:
                if item != "":
                    self.parse_hover_contents(item, render_strings)
        return "\n".join(render_strings)

    def process_response(self, response: dict) -> None:
        if response is None or "contents" not in response or len(response["contents"]) == 0:
            message_emacs("No documentation available.")
            return

        contents = response["contents"]
        render_string = self.parse_hover_contents(contents, [])

        eval_in_emacs("lsp-bridge-popup-documentation--show", render_string)
