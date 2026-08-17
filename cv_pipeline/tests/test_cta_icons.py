import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import render


class CtaIconTests(unittest.TestCase):
    def test_inline_svg_icons_are_materialised_as_embedded_images(self):
        source = f'<a>{render.GITHUB_INLINE_SVG}github</a><a>{render.PORTFOLIO_INLINE_SVG}portfolio</a>'
        output = render._materialise_cta_icons(source)
        self.assertNotIn('<svg class="cta-ico"', output)
        self.assertEqual(2, output.count('data:image/svg+xml;base64,'))
        self.assertIn(render.GITHUB_ICON_DATA, output)
        self.assertIn(render.PORTFOLIO_ICON_DATA, output)
        self.assertEqual(2, output.count('class="cta-ico"'))


if __name__ == "__main__":
    unittest.main()
