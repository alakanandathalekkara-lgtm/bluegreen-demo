pipeline {
  agent any
  parameters {
    booleanParam(name: 'BREAK_RELEASE', defaultValue: false,
                 description: 'Deploy a broken release to test rollback')
  }
  environment {
    APP = 'bg-app'
    NET = 'bg-net'
    STATE_DIR = '/var/lib/jenkins/bluegreen'
    BREAK = "${params.BREAK_RELEASE}"
  }
  stages {
    stage('Checkout') {
      steps { checkout scm }
    }
    stage('Build image') {
      steps { sh 'docker build -t $APP:$BUILD_NUMBER .' }
    }
    stage('Deploy to idle color') {
      steps {
        script {
          def active = sh(script: 'cat $STATE_DIR/active 2>/dev/null || echo none',
                          returnStdout: true).trim()
          env.ACTIVE = active
          env.IDLE = (active == 'blue') ? 'green' : 'blue'
          env.IDLE_PORT = (env.IDLE == 'blue') ? '5001' : '5002'
          echo "Active: ${env.ACTIVE}, deploying to: ${env.IDLE}"
        }
        catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
          sh '''
            mkdir -p $STATE_DIR/nginx
            docker network inspect $NET >/dev/null 2>&1 || docker network create $NET
            docker rm -f app-$IDLE 2>/dev/null || true
            docker run -d --name app-$IDLE --network $NET \
              -p 127.0.0.1:$IDLE_PORT:5000 \
              -e APP_VERSION=$BUILD_NUMBER -e APP_COLOR=$IDLE -e BREAK=$BREAK \
              $APP:$BUILD_NUMBER
          '''
        }
      }
    }
    stage('Smoke tests') {
      when { expression { currentBuild.currentResult == 'SUCCESS' } }
      steps {
        catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
          sh '''
            for i in $(seq 1 15); do
              curl -fsS http://localhost:$IDLE_PORT/health && break
              sleep 2
            done
            curl -fsS http://localhost:$IDLE_PORT/health | grep -q UP
            curl -fsS http://localhost:$IDLE_PORT/ | grep -q "v$BUILD_NUMBER"
          '''
        }
      }
    }
    stage('Switch traffic') {
      when { expression { currentBuild.currentResult == 'SUCCESS' } }
      steps {
        catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
          sh '''
            sed "s/COLOR/$IDLE/" nginx/default.conf.template > $STATE_DIR/nginx/default.conf
            if docker ps -q -f name=bg-router | grep -q .; then
              docker exec bg-router nginx -s reload
            else
              docker run -d --name bg-router --network $NET -p 80:80 \
                -v $STATE_DIR/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro \
                nginx:alpine
            fi
            echo $IDLE > $STATE_DIR/active
          '''
        }
      }
    }
    stage('Verify live traffic') {
      when { expression { currentBuild.currentResult == 'SUCCESS' } }
      steps {
        catchError(buildResult: 'FAILURE', stageResult: 'FAILURE') {
          sh '''
            sleep 3
            curl -fsS http://localhost/ | grep -q "v$BUILD_NUMBER"
          '''
        }
      }
    }
    stage('Rollback') {
      when { expression { currentBuild.currentResult == 'FAILURE' } }
      steps {
        sh '''
          echo "ROLLBACK: release v$BUILD_NUMBER failed"
          if [ "$ACTIVE" != "none" ]; then
            echo "Restoring traffic to $ACTIVE"
            sed "s/COLOR/$ACTIVE/" nginx/default.conf.template > $STATE_DIR/nginx/default.conf
            docker exec bg-router nginx -s reload
            echo $ACTIVE > $STATE_DIR/active
          else
            echo "No previous version, removing router"
            docker rm -f bg-router || true
            rm -f $STATE_DIR/active
          fi
          docker rm -f app-$IDLE || true
        '''
      }
    }
  }
}
