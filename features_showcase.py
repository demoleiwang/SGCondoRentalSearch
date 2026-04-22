"""Feature showcase grid shown on the welcome screen.

One card per major capability, with a clickable example query that
populates the main search box via the existing `_popular_query` session
pattern.
"""

from __future__ import annotations

import streamlit as st

from i18n import t


FEATURES = [
    # (icon, title_key, desc_key, example_label, example_query)
    ("🎯", "features.smart.title", "features.smart.desc",
     "OUE Downtown 2b2b 4500", "OUE Downtown 2b2b 4500"),
    ("🗣️", "features.nl.title", "features.nl.desc",
     "找Bishan附近2房4000以内", "找Bishan附近2房4000以内"),
    ("🏘️", "features.data.title", "features.data.desc",
     "Tampines 5-room 3500", "Tampines 5-room 3500"),
    ("📈", "features.trend.title", "features.trend.desc",
     "Queenstown 1b1b 3300", "Queenstown 1b1b 3300"),
    ("🚇", "features.commute.title", "features.commute.desc",
     "Bishan 2br 4000", "Bishan 2br 4000"),
    ("🧭", "features.filter.title", "features.filter.desc",
     "Novena 1br 3500 south facing high floor",
     "Novena 1br 3500 south facing high floor"),
]


def render(expanded: bool = True) -> None:
    """Render the features showcase as an expander on the welcome screen.

    expanded: expander state. Caller should pass False once a query is active
    so the panel collapses out of the way.
    """
    with st.expander(f"✨ {t('features.heading')}", expanded=expanded):
        st.caption(t("features.subheading"))

        # 2 rows × 3 cols
        for row_start in (0, 3):
            cols = st.columns(3)
            for i in range(3):
                icon, title_k, desc_k, label, query = FEATURES[row_start + i]
                with cols[i]:
                    st.markdown(f"### {icon} {t(title_k)}")
                    st.write(t(desc_k))
                    if st.button(
                        f"▶ {label}",
                        key=f"feature_example_{row_start + i}",
                        use_container_width=True,
                    ):
                        st.session_state["_popular_query"] = query
                        st.rerun()
