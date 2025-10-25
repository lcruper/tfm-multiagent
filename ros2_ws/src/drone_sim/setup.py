from setuptools import setup

package_name = 'drone_sim'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='kapi',
    maintainer_email='lcruper@upo.es',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
	    'follow_waypoints = drone_sim.follow_waypoints:main',
        'stations_rviz = drone_sim.stations_rviz:main',
        'drone_pose_pub = drone_sim.drone_pose_pub:main', 
        ],
    },
)
