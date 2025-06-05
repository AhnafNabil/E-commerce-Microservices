import pulumi
import pulumi_aws as aws

# Configuration
config = pulumi.Config()
git_repo_url = "https://github.com/AhnafNabil/E-commerce-Microservices-AWS.git"
region = "ap-southeast-1"
availability_zones = ["ap-southeast-1a", "ap-southeast-1b"]
ami_id = "ami-0de6806735058f3dc"

# Mailtrap credentials
smtp_user = "8f17fc1a376da4"
smtp_password = "afb5060d93cdaf"

# Base user data script with common functions
base_user_data = """#!/bin/bash
# Update system and install dependencies
apt-get update -y
apt-get install -y docker.io git curl netcat-openbsd jq awscli

# Setup Docker
systemctl start docker
systemctl enable docker
usermod -aG docker ubuntu

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Setup swap space for small instances
sudo mkdir -p /swap && cd /swap || exit
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw defaults 0 0' | sudo tee -a /etc/fstab

# Clone repository
cd /home/ubuntu
git clone %s ecommerce
chown -R ubuntu:ubuntu /home/ubuntu/ecommerce
""" % git_repo_url

# Instance-specific user data scripts
database_user_data = base_user_data + """
# Output private IP for debugging
echo "Database instance private IP: $(hostname -I | awk '{print $1}')"

# Run database setup
cd /home/ubuntu/ecommerce/deploy/aws
chmod +x deploy.sh
chmod +x scripts/*.sh
sudo -u ubuntu bash deploy.sh database
"""

messaging_user_data = base_user_data + """
# Output private IP for debugging
echo "Messaging instance private IP: $(hostname -I | awk '{print $1}')"

# Run messaging setup
cd /home/ubuntu/ecommerce/deploy/aws
chmod +x deploy.sh
chmod +x scripts/*.sh
sudo -u ubuntu bash deploy.sh messaging
"""

# Create a VPC
vpc = aws.ec2.Vpc("ecommerce-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
    tags={"Name": "ecommerce-vpc"}
)

# Create Public Subnets
public_subnet_1 = aws.ec2.Subnet("ecommerce-public-subnet-1",
    vpc_id=vpc.id,
    cidr_block="10.0.1.0/24",
    availability_zone=availability_zones[0],
    map_public_ip_on_launch=True,
    tags={"Name": "ecommerce-public-subnet-1"}
)

public_subnet_2 = aws.ec2.Subnet("ecommerce-public-subnet-2",
    vpc_id=vpc.id,
    cidr_block="10.0.2.0/24",
    availability_zone=availability_zones[1],
    map_public_ip_on_launch=True,
    tags={"Name": "ecommerce-public-subnet-2"}
)

# Create Private Subnets
private_subnet_1 = aws.ec2.Subnet("ecommerce-private-subnet-1",
    vpc_id=vpc.id,
    cidr_block="10.0.3.0/24",
    availability_zone=availability_zones[0],
    tags={"Name": "ecommerce-private-subnet-1"}
)

private_subnet_2 = aws.ec2.Subnet("ecommerce-private-subnet-2",
    vpc_id=vpc.id,
    cidr_block="10.0.4.0/24",
    availability_zone=availability_zones[1],
    tags={"Name": "ecommerce-private-subnet-2"}
)

# Create an Internet Gateway
internet_gateway = aws.ec2.InternetGateway("ecommerce-igw",
    vpc_id=vpc.id,
    tags={"Name": "ecommerce-igw"}
)

# Create an Elastic IP for the NAT Gateway
nat_eip = aws.ec2.Eip("ecommerce-nat-eip",
    domain="vpc",
    tags={"Name": "ecommerce-nat-eip"}
)

# Create a NAT Gateway in Public Subnet 1
nat_gateway = aws.ec2.NatGateway("ecommerce-nat-gateway",
    allocation_id=nat_eip.id,
    subnet_id=public_subnet_1.id,
    tags={"Name": "ecommerce-nat-gateway"},
    opts=pulumi.ResourceOptions(depends_on=[internet_gateway])
)

# Create Route Tables
public_route_table = aws.ec2.RouteTable("ecommerce-public-rt",
    vpc_id=vpc.id,
    tags={"Name": "ecommerce-public-rt"}
)

private_route_table = aws.ec2.RouteTable("ecommerce-private-rt",
    vpc_id=vpc.id,
    tags={"Name": "ecommerce-private-rt"}
)

# Create Routes
public_route = aws.ec2.Route("ecommerce-public-route",
    route_table_id=public_route_table.id,
    destination_cidr_block="0.0.0.0/0",
    gateway_id=internet_gateway.id
)

private_route = aws.ec2.Route("ecommerce-private-route",
    route_table_id=private_route_table.id,
    destination_cidr_block="0.0.0.0/0",
    nat_gateway_id=nat_gateway.id
)

# Associate Route Tables with Subnets
public_rt_assoc_1 = aws.ec2.RouteTableAssociation("ecommerce-public-rt-assoc-1",
    subnet_id=public_subnet_1.id,
    route_table_id=public_route_table.id
)

public_rt_assoc_2 = aws.ec2.RouteTableAssociation("ecommerce-public-rt-assoc-2",
    subnet_id=public_subnet_2.id,
    route_table_id=public_route_table.id
)

private_rt_assoc_1 = aws.ec2.RouteTableAssociation("ecommerce-private-rt-assoc-1",
    subnet_id=private_subnet_1.id,
    route_table_id=private_route_table.id
)

private_rt_assoc_2 = aws.ec2.RouteTableAssociation("ecommerce-private-rt-assoc-2",
    subnet_id=private_subnet_2.id,
    route_table_id=private_route_table.id
)

# Create Security Groups
nginx_sg = aws.ec2.SecurityGroup("ecommerce-nginx-sg",
    vpc_id=vpc.id,
    description="Security group for Nginx gateway instance",
    ingress=[
        {"protocol": "tcp", "from_port": 22, "to_port": 22, "cidr_blocks": ["0.0.0.0/0"]},
        {"protocol": "tcp", "from_port": 80, "to_port": 80, "cidr_blocks": ["0.0.0.0/0"]},
        {"protocol": "tcp", "from_port": 443, "to_port": 443, "cidr_blocks": ["0.0.0.0/0"]}
    ],
    egress=[
        {"protocol": "-1", "from_port": 0, "to_port": 0, "cidr_blocks": ["0.0.0.0/0"]}
    ],
    tags={"Name": "ecommerce-nginx-sg"}
)

microservices_sg = aws.ec2.SecurityGroup("ecommerce-microservices-sg",
    vpc_id=vpc.id,
    description="Security group for microservices instance",
    ingress=[
        {"protocol": "tcp", "from_port": 22, "to_port": 22, "cidr_blocks": ["0.0.0.0/0"]},
        {"protocol": "tcp", "from_port": 8000, "to_port": 8004, "security_groups": [nginx_sg.id]},
        {"protocol": "tcp", "from_port": 8082, "to_port": 8082, "security_groups": [nginx_sg.id]}
    ],
    egress=[
        {"protocol": "-1", "from_port": 0, "to_port": 0, "cidr_blocks": ["0.0.0.0/0"]}
    ],
    tags={"Name": "ecommerce-microservices-sg"}
)

database_sg = aws.ec2.SecurityGroup("ecommerce-database-sg",
    vpc_id=vpc.id,
    description="Security group for database instance",
    ingress=[
        {"protocol": "tcp", "from_port": 22, "to_port": 22, "cidr_blocks": ["0.0.0.0/0"]},
        {"protocol": "tcp", "from_port": 27017, "to_port": 27018, "security_groups": [microservices_sg.id]},
        {"protocol": "tcp", "from_port": 5432, "to_port": 5434, "security_groups": [microservices_sg.id]}
    ],
    egress=[
        {"protocol": "-1", "from_port": 0, "to_port": 0, "cidr_blocks": ["0.0.0.0/0"]}
    ],
    tags={"Name": "ecommerce-database-sg"}
)

messaging_sg = aws.ec2.SecurityGroup("ecommerce-messaging-sg",
    vpc_id=vpc.id,
    description="Security group for messaging systems",
    ingress=[
        {"protocol": "tcp", "from_port": 22, "to_port": 22, "cidr_blocks": ["0.0.0.0/0"]},
        {"protocol": "tcp", "from_port": 5672, "to_port": 5672, "security_groups": [microservices_sg.id]},
        {"protocol": "tcp", "from_port": 15672, "to_port": 15672, "security_groups": [microservices_sg.id]},
        {"protocol": "tcp", "from_port": 9092, "to_port": 9092, "security_groups": [microservices_sg.id]},
        {"protocol": "tcp", "from_port": 29092, "to_port": 29092, "security_groups": [microservices_sg.id]},
        {"protocol": "tcp", "from_port": 2181, "to_port": 2181, "security_groups": [microservices_sg.id]},
        {"protocol": "tcp", "from_port": 6379, "to_port": 6379, "security_groups": [microservices_sg.id]}
    ],
    egress=[
        {"protocol": "-1", "from_port": 0, "to_port": 0, "cidr_blocks": ["0.0.0.0/0"]}
    ],
    tags={"Name": "ecommerce-messaging-sg"}
)

# Create Database Instance
database_instance = aws.ec2.Instance("ecommerce-database",
    instance_type="t2.micro",
    vpc_security_group_ids=[database_sg.id],
    ami=ami_id,
    subnet_id=private_subnet_1.id,
    key_name="EcommerceKeyPair",
    root_block_device={
        "volume_size": 10,
        "volume_type": "gp2"
    },
    user_data=database_user_data,
    user_data_replace_on_change=True,
    tags={
        "Name": "ecommerce-database",
        "Type": "database",
        "Environment": "Testing",
        "Project": "EcommerceMicroservices"
    },
    opts=pulumi.ResourceOptions(depends_on=[
        nat_gateway,
        private_route,
        private_rt_assoc_1
    ])
)

# Create Messaging Instance
messaging_instance = aws.ec2.Instance("ecommerce-messaging",
    instance_type="t2.micro",
    vpc_security_group_ids=[messaging_sg.id],
    ami=ami_id,
    subnet_id=private_subnet_2.id,
    key_name="EcommerceKeyPair",
    root_block_device={
        "volume_size": 10,
        "volume_type": "gp2"
    },
    user_data=messaging_user_data,
    user_data_replace_on_change=True,
    tags={
        "Name": "ecommerce-messaging",
        "Type": "messaging",
        "Environment": "Testing",
        "Project": "EcommerceMicroservices"
    },
    opts=pulumi.ResourceOptions(depends_on=[
        nat_gateway,
        private_route,
        private_rt_assoc_2
    ])
)

# ✅ FIXED: Properly handle Pulumi Outputs using .apply()
microservices_user_data = pulumi.Output.all(
    database_instance.private_ip,
    messaging_instance.private_ip
).apply(lambda args: base_user_data + f"""
# Export essential environment variables - REAL IPs NOW!
export DATABASE_HOST="{args[0]}"
export MESSAGING_HOST="{args[1]}"
export SMTP_USER="{smtp_user}"
export SMTP_PASSWORD="{smtp_password}"

# Debug output to verify variables
echo "DATABASE_HOST set to: $DATABASE_HOST"
echo "MESSAGING_HOST set to: $MESSAGING_HOST"
echo "SMTP_USER set to: $SMTP_USER"

# Add database and messaging hosts to /etc/hosts for easier access
echo "{args[0]} database-host" | tee -a /etc/hosts
echo "{args[1]} messaging-host" | tee -a /etc/hosts

# Create environment file for persistence
cat > /home/ubuntu/service_ips.env << 'EOF'
export DATABASE_HOST="{args[0]}"
export MESSAGING_HOST="{args[1]}"
export SMTP_USER="{smtp_user}"
export SMTP_PASSWORD="{smtp_password}"
EOF
chown ubuntu:ubuntu /home/ubuntu/service_ips.env

# Wait for other instances to be fully ready
sleep 180

# Run microservices setup with explicit environment variables
cd /home/ubuntu/ecommerce/deploy/aws
chmod +x deploy.sh
chmod +x scripts/*.sh
sudo -u ubuntu -E DATABASE_HOST="{args[0]}" MESSAGING_HOST="{args[1]}" SMTP_USER="{smtp_user}" SMTP_PASSWORD="{smtp_password}" bash deploy.sh microservices
""")

# Create Microservices Instance
microservices_instance = aws.ec2.Instance("ecommerce-microservices",
    instance_type="t2.micro",
    vpc_security_group_ids=[microservices_sg.id],
    ami=ami_id,
    subnet_id=public_subnet_1.id,
    key_name="EcommerceKeyPair",
    associate_public_ip_address=True,
    root_block_device={
        "volume_size": 10,
        "volume_type": "gp2"
    },
    user_data=microservices_user_data,
    user_data_replace_on_change=True,
    tags={
        "Name": "ecommerce-microservices",
        "Type": "microservices",
        "Environment": "Testing",
        "Project": "EcommerceMicroservices"
    },
    opts=pulumi.ResourceOptions(depends_on=[
        database_instance,
        messaging_instance
    ])
)

# ✅ FIXED: Nginx user data with proper Output handling
nginx_user_data_updated = microservices_instance.private_ip.apply(
    lambda microservices_ip: base_user_data + f"""
# Export microservices host for nginx configuration
export MICROSERVICES_HOST="{microservices_ip}"

# Debug output
echo "MICROSERVICES_HOST set to: $MICROSERVICES_HOST"

# Add microservices host to /etc/hosts
echo "{microservices_ip} microservices-host" | tee -a /etc/hosts

# Wait for microservices to be ready
sleep 240

# Run nginx setup
cd /home/ubuntu/ecommerce/deploy/aws
chmod +x deploy.sh
chmod +x scripts/*.sh
sudo -u ubuntu -E MICROSERVICES_HOST="{microservices_ip}" bash deploy.sh nginx
"""
)

# Create Nginx Instance
nginx_instance = aws.ec2.Instance("ecommerce-nginx",
    instance_type="t2.micro",
    vpc_security_group_ids=[nginx_sg.id],
    ami=ami_id,
    subnet_id=public_subnet_2.id,
    key_name="EcommerceKeyPair",
    associate_public_ip_address=True,
    root_block_device={
        "volume_size": 8,
        "volume_type": "gp2"
    },
    user_data=nginx_user_data_updated,
    user_data_replace_on_change=True,
    tags={
        "Name": "ecommerce-nginx",
        "Type": "nginx",
        "Environment": "Testing",
        "Project": "EcommerceMicroservices"
    },
    opts=pulumi.ResourceOptions(depends_on=[
        microservices_instance
    ])
)

# Export Outputs
pulumi.export("vpc_id", vpc.id)
pulumi.export("public_subnet_1_id", public_subnet_1.id)
pulumi.export("public_subnet_2_id", public_subnet_2.id)
pulumi.export("private_subnet_1_id", private_subnet_1.id)
pulumi.export("private_subnet_2_id", private_subnet_2.id)
pulumi.export("microservices_instance_id", microservices_instance.id)
pulumi.export("microservices_instance_private_ip", microservices_instance.private_ip)
pulumi.export("microservices_instance_public_ip", microservices_instance.public_ip)
pulumi.export("database_instance_id", database_instance.id)
pulumi.export("database_instance_private_ip", database_instance.private_ip)
pulumi.export("nginx_instance_id", nginx_instance.id)
pulumi.export("nginx_instance_public_ip", nginx_instance.public_ip)
pulumi.export("messaging_instance_id", messaging_instance.id)
pulumi.export("messaging_instance_private_ip", messaging_instance.private_ip)