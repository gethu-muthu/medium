import kopf
import kubernetes
from kubernetes import client, config

@kopf.on.startup()
def configure(settings: kopf.OperatorSettings, **_):
    settings.persistence.finalizer = 'memory-optimizer.example.com/finalizer'

@kopf.on.create('optimize.k8s.example.com', 'v1alpha1', 'memoryoptimizers')
def on_create(spec, name, namespace, **kwargs):
    min_threshold = spec.get('minMemoryThreshold', 0.7)
    max_downscale = spec.get('maxDownscalePercent', 0.3)
    observation_period = spec.get('observationPeriod', '7d')

    # Memory usage tracking logic
    def track_memory_usage(pod):
        container_stats = collect_container_memory_metrics(pod)
        recommendations = calculate_recommendations(
            container_stats, 
            min_threshold, 
            max_downscale
        )
        update_pod_annotations(pod, recommendations)

@kopf.on.periodic(interval=3600)  # Run every hour
def optimize_memory_usage(**kwargs):
    # Global cluster-wide memory optimization
    v1 = client.CoreV1Api()
    pods = v1.list_pod_for_all_namespaces()
    
    for pod in pods.items:
        analyze_and_optimize_pod(pod) 
		
		

def calculate_recommendations(container_stats, min_threshold, max_downscale):
    """
    Calculate safe memory recommendations for containers
    
    Args:
        container_stats (dict): Memory usage statistics
        min_threshold (float): Minimum memory retention percentage
        max_downscale (float): Maximum allowed downscaling percentage
    
    Returns:
        dict: Recommended memory configurations
    """
    recommendations = {}
    for container, stats in container_stats.items():
        peak_memory = stats['peak_usage']
        current_limit = stats['current_limit']
        
        # Calculate recommended memory
        recommended_memory = max(
            peak_memory * (1 + min_threshold),
            current_limit * (1 - max_downscale)
        )
        
        recommendations[container] = {
            'recommended_limit': recommended_memory,
            'current_usage_percent': stats['usage_percent']
        }
    
    return recommendations

def update_pod_annotations(pod, recommendations):
    """
    Update pod annotations with memory optimization recommendations
    """
    annotations = pod.metadata.annotations or {}
    annotations.update({
        'memory-optimizer.example.com/recommendations': json.dumps(recommendations)
    })
    pod.metadata.annotations = annotations