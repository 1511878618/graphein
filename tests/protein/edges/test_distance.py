"""Functions for working with Protein Structure Graphs. Based on tests written by Eric Ma in PIN Library"""
from functools import partial

# %%
# Graphein
# Author: Arian Jamasb <arian@jamasb.io>, Eric Ma, Charlie Harris
# License: MIT
# Project Website: https://github.com/a-r-j/graphein
# Code Repository: https://github.com/a-r-j/graphein
from pathlib import Path

import pytest

import graphein.protein as gp
from graphein.protein.config import ProteinGraphConfig
from graphein.protein.edges.distance import (
    add_salt_bridges,
    add_sequence_distance_edges,
    add_vdw_clashes,
    add_vdw_interactions,
    get_edges_by_bond_type,
    get_ring_atoms,
    get_ring_centroids,
)
from graphein.protein.graphs import construct_graph, read_pdb_to_dataframe
from graphein.protein.resi_atoms import (
    AROMATIC_RESIS,
    BOND_TYPES,
    CATION_RESIS,
    HYDROPHOBIC_RESIS,
    NEG_AA,
    PI_RESIS,
    POS_AA,
    RESI_NAMES,
    SALT_BRIDGE_ANIONS,
    SALT_BRIDGE_CATIONS,
    SULPHUR_RESIS,
    VDW_RADII,
)

DATA_PATH = Path(__file__).resolve().parent.parent / "test_data" / "4hhb.pdb"


def generate_graph():
    """Generate PDB network.
    This is a helper function.
    """
    return construct_graph(pdb_path=str(DATA_PATH))


@pytest.fixture(scope="module")
def net():
    """Generate proteingraph from 2VUI.pdb."""
    return generate_graph()


@pytest.fixture()
def pdb_df():
    """Generate pdb_df from 2VIU.pdb."""
    return read_pdb_to_dataframe(DATA_PATH)


def test_nodes_are_strings(net):
    """
    Checks to make sure that the nodes are a string.
    For expediency, checks only 1/4 of the nodes.
    """
    for n in net.nodes():
        assert isinstance(n, str)


def test_add_hydrophobic_interactions(net):
    """Test the function add_hydrophobic_interactions_."""
    resis = get_edges_by_bond_type(net, "hydrophobic")
    for (r1, r2) in resis:
        assert net.nodes[r1]["residue_name"] in HYDROPHOBIC_RESIS
        assert net.nodes[r2]["residue_name"] in HYDROPHOBIC_RESIS


def test_add_disulfide_interactions(net):
    """Test the function add_disulfide_interactions_."""
    resis = get_edges_by_bond_type(net, "disulfide")

    for (r1, r2) in resis:
        assert net.nodes[r1]["residue_name"] == "CYS"
        assert net.nodes[r2]["residue_name"] == "CYS"


@pytest.mark.skip(reason="Not yet implemented.")
def test_delaunay_triangulation(net):
    """
    Test delaunay triangulation.
    I am including this test here that always passes because I don't know how
    best to test it. The code in pin.py uses scipy's delaunay triangulation.
    """
    pass


@pytest.mark.skip(reason="Implementation needs to be checked.")
def test_add_hydrogen_bond_interactions(net):
    """Test that the addition of hydrogen bond interactions works correctly."""
    pass


def test_add_aromatic_interactions(net):
    """
    Tests the function add_aromatic_interactions_.
    The test checks that each residue in an aromatic interaction
    is one of the aromatic residues.
    """
    resis = get_edges_by_bond_type(net, "aromatic")
    for n1, n2 in resis:
        assert net.nodes[n1]["residue_name"] in AROMATIC_RESIS
        assert net.nodes[n2]["residue_name"] in AROMATIC_RESIS


def test_add_aromatic_sulphur_interactions(net):
    """Tests the function add_aromatic_sulphur_interactions_."""
    resis = get_edges_by_bond_type(net, "aromatic_sulphur")
    for n1, n2 in resis:
        condition1 = (
            net.nodes[n1]["residue_name"] in SULPHUR_RESIS
            and net.nodes[n2]["residue_name"] in AROMATIC_RESIS
        )

        condition2 = (
            net.nodes[n2]["residue_name"] in SULPHUR_RESIS
            and net.nodes[n1]["residue_name"] in AROMATIC_RESIS
        )

        assert condition1 or condition2


def test_add_ionic_interactions(net):
    """
    Tests the function add_ionic_interactions_.
    This test checks that residues involved in ionic interactions
    are indeed oppositely-charged.
    Another test is needed to make sure that ionic interactions
    are not missed.
    """
    resis = get_edges_by_bond_type(net, "ionic")
    for n1, n2 in resis:
        resi1 = net.nodes[n1]["residue_name"]
        resi2 = net.nodes[n2]["residue_name"]

        condition1 = resi1 in POS_AA and resi2 in NEG_AA
        condition2 = resi2 in POS_AA and resi1 in NEG_AA

        assert condition1 or condition2


@pytest.mark.skip(reason="Not yet implemented.")
def test_get_ring_centroids(pdb_df):
    """Test the function get_ring_centroids."""
    print(pdb_df)
    ring_atom_TYR = get_ring_atoms(pdb_df, "TYR")
    assert len(ring_atom_TYR) == 32
    centroid_TYR = get_ring_centroids(ring_atom_TYR)
    assert len(centroid_TYR) == 16

    ring_atom_PHE = get_ring_atoms(pdb_df, "PHE")
    assert len(ring_atom_PHE) == 36
    centroid_PHE = get_ring_centroids(ring_atom_PHE)
    assert len(centroid_PHE) == 18


def test_add_cation_pi_interactions(net):
    """Tests the function add_cation_pi_interactions."""
    resis = get_edges_by_bond_type(net, "cation_pi")
    for n1, n2 in resis:
        resi1 = net.nodes[n1]["residue_name"]
        resi2 = net.nodes[n2]["residue_name"]

        condition1 = resi1 in CATION_RESIS and resi2 in PI_RESIS
        condition2 = resi2 in CATION_RESIS and resi1 in PI_RESIS

        assert condition1 or condition2


def test_add_peptide_bonds():
    file_path = Path(__file__).parent.parent / "test_data/4hhb.pdb"
    # Peptide bonds are default
    G = construct_graph(pdb_path=str(file_path))

    for u, v in G.edges():
        assert abs(int(u.split(":")[-1]) - int(v.split(":")[-1])) == 1


def test_add_sequence_distance_edges():
    D = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    file_path = Path(__file__).parent.parent / "test_data/4hhb.pdb"

    for d in D:
        config = ProteinGraphConfig(
            edge_construction_functions=[
                partial(add_sequence_distance_edges, d=d)
            ]
        )
        G = construct_graph(pdb_path=str(file_path), config=config)
        for u, v in G.edges():
            assert abs(int(u.split(":")[-1]) - int(v.split(":")[-1])) == d


def test_salt_bridge_interactions():
    """
    Test to ensure salt bridges are only between anionic and cationic residues.
    Also checks distances are correct on atom graphs.
    """
    g = construct_graph(
        pdb_code="216L",
        config=ProteinGraphConfig(
            edge_construction_functions=[add_salt_bridges]
        ),
    )
    for u, v, d in g.edges(data=True):
        assert "salt_bridge" in d["kind"]
        res1 = g.nodes[u]["residue_name"]
        res2 = g.nodes[v]["residue_name"]

        assert (
            res1 in SALT_BRIDGE_CATIONS and res2 in SALT_BRIDGE_ANIONS
        ) or (
            res1 in SALT_BRIDGE_ANIONS and res2 in SALT_BRIDGE_CATIONS
        ), "Salt bridge not between cations and anions"

    # Test distances on atom graphs
    g = construct_graph(
        pdb_code="216L",
        config=ProteinGraphConfig(
            edge_construction_functions=[add_salt_bridges], granularity="atom"
        ),
    )
    for u, v, d in g.edges(data=True):
        assert "salt_bridge" in d["kind"]
        res1 = g.nodes[u]["residue_name"]
        res2 = g.nodes[v]["residue_name"]

        assert (
            res1 in SALT_BRIDGE_CATIONS and res2 in SALT_BRIDGE_ANIONS
        ) or (
            res1 in SALT_BRIDGE_ANIONS and res2 in SALT_BRIDGE_CATIONS
        ), "Salt bridge not between cations and anions"
        assert d["distance"] < 4.0, "Salt bridge distance is too long"


def test_vdw_interactions():
    """
    Test to ensure vdw interactions are identified and are of correct length in
    atomic graphs.
    """
    g = construct_graph(
        pdb_code="216L",
        config=ProteinGraphConfig(
            edge_construction_functions=[add_vdw_interactions]
        ),
    )
    for u, v, d in g.edges(data=True):
        assert "vdw" in d["kind"], "Edge not vdw"

    # Test distances on atom graphs
    g = construct_graph(
        pdb_code="216L",
        config=ProteinGraphConfig(
            edge_construction_functions=[add_vdw_interactions],
            granularity="atom",
        ),
    )
    for u, v, d in g.edges(data=True):
        assert "vdw" in d["kind"]
        res1 = g.nodes[u]["element_symbol"]
        res2 = g.nodes[v]["element_symbol"]
        rad1 = VDW_RADII[res1]
        rad2 = VDW_RADII[res2]

        assert res1 != "H" and res2 != "H", "Hydrogen in vdw interaction"
        assert (
            d["distance"] < 0.5 + rad1 + rad2
        ), f"Vdw distance is too long: {d['distance']}"


def test_vdw_clashes():
    """
    Test to ensure vdw clashes are identified and are of correct length in
    atomic graphs.
    """
    g = construct_graph(
        pdb_code="216L",
        config=ProteinGraphConfig(
            edge_construction_functions=[add_vdw_clashes]
        ),
    )
    for u, v, d in g.edges(data=True):
        assert "vdw_clash" in d["kind"], "Edge not vdw_clash"

    # Test distances on atom graphs
    g = gp.construct_graph(
        pdb_code="216L",
        config=gp.ProteinGraphConfig(
            edge_construction_functions=[add_vdw_clashes],
            granularity="atom",
        ),
    )
    for u, v, d in g.edges(data=True):
        assert "vdw_clash" in d["kind"]
        res1 = g.nodes[u]["element_symbol"]
        res2 = g.nodes[v]["element_symbol"]
        rad1 = VDW_RADII[res1]
        rad2 = VDW_RADII[res2]

        assert res1 != "H" and res2 != "H", "Hydrogen in vdw clash interaction"
        assert (
            d["distance"] < rad1 + rad2
        ), f"Vdw clash distance is too long: {d['distance']}"
