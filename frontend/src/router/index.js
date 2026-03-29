import { createRouter, createWebHistory } from 'vue-router'
import ConnectionList from '../views/ConnectionList.vue'
import ConnectionDetail from '../views/ConnectionDetail.vue'
import Settings from '../views/Settings.vue'
import Topology from '../views/Topology.vue'

const routes = [
  {
    path: '/',
    name: 'ConnectionList',
    component: ConnectionList
  },
  {
    path: '/connection/:name',
    name: 'ConnectionDetail',
    component: ConnectionDetail
  },
  {
    path: '/topology',
    name: 'Topology',
    component: Topology
  },
  {
    path: '/settings',
    name: 'Settings',
    component: Settings
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
