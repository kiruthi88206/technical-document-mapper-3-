/**
 * Vis.js Knowledge Graph Visualization Controller
 * Manages rendering, physics simulation, node/edge interactions, and camera controls.
 */
class KnowledgeGraphViewer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.network = null;
        this.nodesDataSet = new vis.DataSet([]);
        this.edgesDataSet = new vis.DataSet([]);
        this.rawNodes = [];
        this.rawEdges = [];
        this.physicsEnabled = true;
        this.hierarchicalEnabled = false;
        this.onNodeSelectedCallback = null;

        this.defaultOptions = {
            nodes: {
                shape: 'dot',
                size: 26,
                borderWidth: 2,
                font: {
                    color: '#F8FAFC',
                    size: 13,
                    face: 'Inter, system-ui, sans-serif'
                },
                shadow: {
                    enabled: true,
                    color: 'rgba(0, 0, 0, 0.45)',
                    size: 7,
                    x: 2,
                    y: 2
                }
            },
            edges: {
                arrows: {
                    to: { enabled: true, scaleFactor: 0.8 }
                },
                color: {
                    color: '#475569',
                    highlight: '#38BDF8',
                    hover: '#818CF8'
                },
                font: {
                    color: '#94A3B8',
                    size: 10,
                    strokeWidth: 2,
                    strokeColor: '#0B0F19',
                    align: 'middle'
                },
                smooth: {
                    type: 'continuous',
                    roundness: 0.15
                }
            },
            physics: {
                enabled: true,
                barnesHut: {
                    gravitationalConstant: -3800,
                    centralGravity: 0.35,
                    springLength: 130,
                    springConstant: 0.04,
                    damping: 0.09,
                    avoidOverlap: 0.3
                },
                stabilization: {
                    enabled: true,
                    iterations: 120,
                    updateInterval: 25
                }
            },
            interaction: {
                hover: true,
                tooltipDelay: 100,
                hideEdgesOnDrag: false,
                navigationButtons: false,
                zoomView: true,
                dragView: true
            }
        };
    }

    initNetwork(nodes, edges) {
        this.rawNodes = nodes || [];
        this.rawEdges = edges || [];

        this.nodesDataSet.clear();
        this.edgesDataSet.clear();

        this.nodesDataSet.add(this.rawNodes);
        this.edgesDataSet.add(this.rawEdges);

        const data = {
            nodes: this.nodesDataSet,
            edges: this.edgesDataSet
        };

        if (this.network) {
            this.network.destroy();
        }

        this.network = new vis.Network(this.container, data, this.defaultOptions);
        this._bindEvents();

        // Fit after initial stabilization
        this.network.once('stabilizationIterationsDone', () => {
            this.network.fit({ animation: { duration: 600, easingFunction: 'easeInOutQuad' } });
        });
    }

    _bindEvents() {
        if (!this.network) return;

        this.network.on('click', (params) => {
            if (params.nodes.length > 0) {
                const selectedNodeId = params.nodes[0];
                const nodeData = this.nodesDataSet.get(selectedNodeId);
                
                // Get connected edges and neighbor nodes
                const connectedEdgeIds = this.network.getConnectedEdges(selectedNodeId);
                const connectedEdges = this.edgesDataSet.get(connectedEdgeIds);
                const connectedNodeIds = this.network.getConnectedNodes(selectedNodeId);
                const connectedNodes = this.nodesDataSet.get(connectedNodeIds);

                if (this.onNodeSelectedCallback) {
                    this.onNodeSelectedCallback({
                        node: nodeData,
                        edges: connectedEdges,
                        neighbors: connectedNodes
                    });
                }
            }
        });

        this.network.on('doubleClick', (params) => {
            if (params.nodes.length > 0) {
                this.focusOnNode(params.nodes[0]);
            }
        });
    }

    setOnNodeSelected(callback) {
        this.onNodeSelectedCallback = callback;
    }

    zoomIn() {
        if (!this.network) return;
        const currentScale = this.network.getScale();
        this.network.moveTo({ scale: currentScale * 1.3, animation: { duration: 250 } });
    }

    zoomOut() {
        if (!this.network) return;
        const currentScale = this.network.getScale();
        this.network.moveTo({ scale: currentScale * 0.75, animation: { duration: 250 } });
    }

    fitToScreen() {
        if (!this.network) return;
        this.network.fit({ animation: { duration: 500, easingFunction: 'easeInOutQuad' } });
    }

    resetView() {
        if (!this.network) return;
        this.network.fit({ animation: { duration: 400 } });
        this.network.unselectAll();
    }

    togglePhysics() {
        if (!this.network) return false;
        this.physicsEnabled = !this.physicsEnabled;
        this.network.setOptions({ physics: { enabled: this.physicsEnabled } });
        return this.physicsEnabled;
    }

    toggleHierarchy() {
        if (!this.network) return false;
        this.hierarchicalEnabled = !this.hierarchicalEnabled;
        
        const options = {
            layout: {
                hierarchical: {
                    enabled: this.hierarchicalEnabled,
                    direction: 'UD',
                    sortMethod: 'directed',
                    levelSeparation: 120,
                    nodeSpacing: 100
                }
            },
            physics: {
                hierarchicalRepulsion: {
                    nodeDistance: 120
                }
            }
        };
        this.network.setOptions(options);
        this.fitToScreen();
        return this.hierarchicalEnabled;
    }

    focusOnNode(nodeId) {
        if (!this.network) return;
        this.network.selectNodes([nodeId]);
        this.network.focus(nodeId, {
            scale: 1.25,
            animation: {
                duration: 600,
                easingFunction: 'easeInOutQuad'
            }
        });
    }

    highlightSearch(searchTerm) {
        if (!this.network || !searchTerm) return null;
        const termLower = searchTerm.toLowerCase().trim();

        const allNodes = this.nodesDataSet.get();
        const matched = allNodes.find(n => 
            n.label.toLowerCase().includes(termLower) || 
            (n.category && n.category.toLowerCase().includes(termLower))
        );

        if (matched) {
            this.focusOnNode(matched.id);
            const connectedEdges = this.edgesDataSet.get(this.network.getConnectedEdges(matched.id));
            const connectedNodes = this.nodesDataSet.get(this.network.getConnectedNodes(matched.id));

            if (this.onNodeSelectedCallback) {
                this.onNodeSelectedCallback({
                    node: matched,
                    edges: connectedEdges,
                    neighbors: connectedNodes
                });
            }
            return matched;
        }
        return null;
    }

    capturePng() {
        if (!this.container) return;
        const canvas = this.container.querySelector('canvas');
        if (!canvas) return;

        const imageUri = canvas.toDataURL('image/png');
        const link = document.createElement('a');
        link.download = `knowledge_graph_${Date.now()}.png`;
        link.href = imageUri;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}
