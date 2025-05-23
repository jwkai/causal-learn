import itertools
from causallearn.graph.Graph import Graph


class SCM:
    """
    Compute the s/c-metrics between two graphs. These represent violations of 
    faithfulness (s-metric, "false pos") and Markovian (c-metric, "false neg") 
    assumptions for the estimated graph relative to the ground truth graph. 
    The s/c-metric weighs both violations equally.
    """
    def __init__(self, truth: Graph, est: Graph):
        """
        Compute and store s/c-metrics between two graphs (rel. to truth graph).
        (Warning: exponential algorithm in # nodes, may take several minutes!)

        Parameters
        ----------
        truth : Graph
            Truth graph.
        est : Graph
            Estimated graph.
        """
        truth_node_map = {node.get_name(): node_id for node, node_id in truth.node_map.items()}
        est_node_map = {node.get_name(): node_id for node, node_id in est.node_map.items()}
        assert set(truth_node_map.keys()) == set(est_node_map.keys()), "The two graphs have different sets of node names."

        self.__SM: float = 0.0
        self.__CM: float = 0.0
        self.__SCM: float = 0.0
        
        N = truth.get_num_nodes()
        # Compute the s/c-metrics of order K up to N-2
        for k in range(1, N-1):
            SM_k: float = 0.0
            CM_k: float = 0.0
            SCM_k: float = 0.0
            n_C_k_con = 0
            n_C_k_sep = 0
            # Triples (X,Y,S) where X,Y in V, X =/= Y, S subset V\{X,Y}, |S|=k
            S_sets = itertools.combinations(truth_node_map.items(), k)
            for S in S_sets:
                S_names = [t[0] for t in S]
                truth_S_nodes = [truth.get_node(t[0]) for t in S]
                est_S_nodes = [est.get_node(t[0]) for t in S]
                for x_name, _ in truth_node_map.items():
                    if x_name in S_names: continue
                    truth_x_node = truth.get_node(x_name)
                    est_x_node = est.get_node(x_name)
                    for y_name, _ in truth_node_map.items():
                        if y_name in S_names: continue
                        if x_name == y_name: continue
                        truth_y_node = truth.get_node(y_name)
                        est_y_node = est.get_node(y_name)
                        # Determine d-connection/d-separation for each triple
                        truth_i_con = truth.is_dconnected_to(truth_x_node, truth_y_node, truth_S_nodes)
                        est_i_con = est.is_dconnected_to(est_x_node, est_y_node, est_S_nodes)
                        # Increment s/c-m if truth and est disagree on d-sep
                        SCM_k = SCM_k + (1.0 if (truth_i_con != est_i_con) else 0.0)
                        if truth_i_con:
                            # Increment c-m if est missing a d-con in truth
                            CM_k = CM_k + (0.0 if est_i_con else 1.0)
                            n_C_k_con = n_C_k_con + 1
                        else:
                            # Increment s-m if est missing a d-sep in truth
                            SM_k = SM_k + (1.0 if est_i_con else 0.0)
                            n_C_k_sep = n_C_k_sep + 1
            # Normalize: # of connections/separations/all triples respectively
            self.__SM = self.__SM + (SM_k / n_C_k_sep)
            self.__CM = self.__CM + (SM_k / n_C_k_con)      
            self.__SCM = self.__SCM + (SCM_k / (n_C_k_sep + n_C_k_con))
        # Average across all s/c^K-metrics
        self.__SM = self.__SM / (N-1)
        self.__CM = self.__CM / (N-1)
        self.__SCM = self.__SCM / (N-1)
                            

    def get_s_metric(self) -> float:
        return self.__SM

    def get_c_metric(self) -> float:
        return self.__CM
        
    def get_sc_metric(self) -> float:
        return self.__SCM