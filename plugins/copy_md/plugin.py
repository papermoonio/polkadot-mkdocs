import os
import shutil
from mkdocs.plugins import BasePlugin
from mkdocs.config.config_options import Type

class CopyMDPlugin(BasePlugin):
    config_scheme = (
        ("source_dir", Type(str, required=True)),
        ("target_dir", Type(str, required=True)),
    )

    def on_post_build(self, config):
        source = self.config['source_dir']
        target = os.path.join(config['site_dir'], self.config['target_dir'])

        if not os.path.exists(source):
            print(f"[copy-md] Source directory '{source}' not found; skipping.")
            return

        # Remove existing target if present to avoid stale files
        if os.path.exists(target):
            shutil.rmtree(target)

        shutil.copytree(source, target)
        print(f"[copy-md] Copied raw Markdown from '{source}' to '{target}'")
