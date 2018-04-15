provider "aws" {
    region = "us-east-1"
}

# TODO: Security groups, VPCs, R53 zone and record

resource "aws_elb" "web" {
    name = "hello-elb"
    availability_zones = ["${aws_instance.web.*.availability_zone}"]
    instances = ["${aws_instance.web.*.id}"]

    listener {
        instance_port = 5000
        instance_protocol = "http"
        lb_port = 80
        lb_protocol = "http"
    }

    health_check {
        healthy_threshold = 2
        unhealthy_threshold = 2
        timeout = 2
        target = "HTTP:5000/healthcheck"
        interval = 5
    }
}

resource "aws_instance" "web" {
    ami = "ami-74e6b80d"
    instance_type = "t2.nano"
    key_name = "mgorven-mamma"
    # TODO: Spread over AZs for redundancy
    # TODO: Autoscaling
    count = 2

    provisioner "remote-exec" {
        inline = [
            "sudo apt-get update && sudo apt-get -y install python3-virtualenv",
            "sudo adduser --disabled-password --gecos 'web,,,,,' web",
            "cd /home/web && sudo virtualenv -p python3 venv",
            "cd /home/web && sudo git checkout --depth=1 https://github.com/mgorven/hello.git",
            "sudo /home/web/venv/bin/pip pip install -r /home/web/hello/requirements.txt",
            "echo 'SQLALCHEMY_DATABASE_URI=\"mysql://${aws_db_instance.hello.username}:${aws_db_instance.hello.password}@${aws_db_instance.hello.address}/${aws_db_instance.hello.name}\"' | sudo tee /home/web/hello/prod.cfg",
            # TODO: Only run DB creation once
            "cd /home/web/hello && sudo -u web FLASK_CONFIG=prod.cfg /home/web/venv/bin/python -c 'import hello; hello.db.create_all()'",
            # TODO: Use a proper application runner like uWSGI/Gunicorn
            "echo 'cd /home/web/hello && sudo -u web FLASK_APP=hello.py FLASK_CONFIG=prod.cfg /home/web/venv/bin/flask run -h :: --with-threads &' >> /etc/rc.local",
            # TODO: Use a systemd unit
            "sudo /etc/rc.local",
        ]
        connection {
            type = "ssh"
            user = "ubuntu"
        }
    }
}

resource "aws_db_instance" "hello" {
    allocated_storage = 1
    storage_type = "standard"
    engine = "mysql"
    instance_class = "db.t2.micro"
    name = "hello"
    username = "web"
    password = "ZvlPwBP8HKLbC0cj"
    # TODO: Multi-AZ, backups
}
